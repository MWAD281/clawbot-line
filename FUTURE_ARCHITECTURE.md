# Future Architecture

## Current Architecture (2026-05)

```
LINE Platform → POST /callback
    └── FastAPI (Render, single instance)
          ├── Sig verification
          ├── Rate limit (slowapi, in-memory)
          ├── BackgroundTask → OpenAI → LINE Reply API
          └── In-memory conversation store (Redis optional)
```

**Limitations:** Single instance, in-memory rate-limiter doesn't work across replicas, no message queue, no persistent user data, no observability beyond logs.

---

## Near-Term Architecture (Phase 2–3)

```
LINE Platform → POST /callback
    └── FastAPI (2+ Render/Railway instances behind load balancer)
          ├── Sig verification
          ├── Rate limit (slowapi + Redis backend → works across replicas)
          └── Enqueue to Redis Streams / Celery

Redis Streams / Celery Worker
    ├── Dequeue message
    ├── Check daily limit (PostgreSQL)
    ├── Fetch conversation history (Redis, 24h TTL)
    ├── Trim to token budget
    ├── Call OpenAI (with retry + circuit breaker)
    ├── Store assistant reply in history
    ├── Increment usage counter
    └── Send LINE reply

PostgreSQL
    ├── users(line_user_id, tier, credits, created_at)
    ├── messages(id, user_id, role, content, tokens, created_at)  ← audit log
    └── tenants(id, channel_secret, channel_token, system_prompt, plan)

pgvector (same PostgreSQL)
    └── embeddings(id, tenant_id, content, embedding vector)  ← RAG

Admin API (separate FastAPI app or Django)
    ├── GET /admin/stats
    ├── POST /admin/users/{id}/upgrade
    └── GET /admin/tenants
```

---

## Target Architecture (Phase 4, Multi-Tenant Scale)

```
                    ┌─────────────────────────────────────────┐
                    │           LINE Platform                  │
                    └──────────────┬──────────────────────────┘
                                   │ POST /callback (per tenant OA)
                    ┌──────────────▼──────────────────────────┐
                    │      API Gateway / Nginx / Cloudflare    │
                    │      (TLS termination, DDoS protection)  │
                    └──────────────┬──────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
    ┌─────────▼──────┐  ┌──────────▼──────┐  ┌────────▼────────┐
    │  Webhook API   │  │  Webhook API    │  │  Webhook API    │
    │  (FastAPI)     │  │  (FastAPI)      │  │  (FastAPI)      │
    └────────┬───────┘  └────────┬────────┘  └────────┬────────┘
             │                   │                    │
             └───────────────────┼────────────────────┘
                                 │ enqueue
                    ┌────────────▼────────────────────┐
                    │         Redis Streams            │
                    └────────────┬────────────────────┘
                                 │ consume
              ┌──────────────────┼──────────────────────┐
              │                  │                      │
    ┌─────────▼──────┐  ┌────────▼────────┐  ┌────────▼────────┐
    │  AI Worker     │  │  AI Worker      │  │  AI Worker      │
    │  (Celery)      │  │  (Celery)       │  │  (Celery)       │
    └────────┬───────┘  └────────┬────────┘  └────────┬────────┘
             │                   │                    │
             └───────────────────┼────────────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
    ┌─────▼──────┐      ┌────────▼────────┐    ┌───────▼────────┐
    │ PostgreSQL │      │  Redis Cache    │    │  OpenAI API /  │
    │ + pgvector │      │  (history,      │    │  Claude API /  │
    │ (users,    │      │   rate limits,  │    │  Gemini API    │
    │  messages, │      │   sessions)     │    │  (multi-model) │
    │  tenants,  │      └─────────────────┘    └────────────────┘
    │  RAG)      │
    └────────────┘

    ┌─────────────────────────────────────────┐
    │         Observability Layer             │
    │  Sentry (errors) + Datadog/Grafana      │
    │  (metrics) + OpenTelemetry (traces)     │
    └─────────────────────────────────────────┘
```

---

## Key Architectural Decisions for Scale

### 1. Decouple webhook from AI call (Redis Streams / Celery)
- **Why:** OpenAI calls take 1–10s. LINE requires 200ms acknowledgement. BackgroundTasks works on a single instance but breaks under high load or multi-replica deploys. A proper queue decouples the two and enables retries without duplicate replies.
- **When to do it:** When you have >100 concurrent users or are seeing LINE timeout errors.

### 2. PostgreSQL for durable storage
- **Why:** Redis TTL means conversation history is lost. User payment records, audit logs, and RAG embeddings all need durable storage.
- **When to do it:** Before charging any money — you need a `users` table.

### 3. Multi-model abstraction
- **Why:** Single LLM provider is a concentration risk. Price changes, outages, and rate limits all create business risk.
- **How:** Abstract `chat_completion()` behind a model-agnostic interface; route by tier (gpt-4o-mini for free, claude-opus for premium).

### 4. Multi-tenant from the start of B2B
- **Why:** Each LINE OA (business) has its own channel secret, access token, and system prompt. You need a `tenants` table and per-request tenant resolution before your first B2B customer.
- **How:** Resolve tenant from the `X-Line-Signature` channel secret or a URL prefix.

### 5. pgvector for RAG
- **Why:** A general chat bot has poor retention. A bot that knows your restaurant's menu, clinic's FAQs, or store's return policy has high retention. pgvector keeps RAG in the same database as your user data — no extra infrastructure.
- **When to do it:** Phase 2, after first paying B2B customer.

---

## Technology Decisions to Avoid

| Don't | Why |
|-------|-----|
| MongoDB | No transactions; pgvector is better for embeddings |
| LangChain in production | Heavy, opaque, version-unstable; use it for prototyping only |
| Kubernetes before ฿200k MRR | Operational overhead not justified; Railway/Render scales far enough |
| Fine-tuning before RAG | RAG is faster, cheaper, and updatable; fine-tune only for style/persona |
| Multiple microservices before 10k users | Monolith first; split only when you have clear seams and real load |
