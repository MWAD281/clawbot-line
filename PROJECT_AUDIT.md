# PROJECT AUDIT — clawbot-line
**Auditor:** Senior AI Engineer / Backend Architect  
**Date:** 2026-05-07  
**Verdict:** Not production-ready. Ship-blocker issues exist. The codebase is a chimera of two unrelated systems sharing a repository.

---

## 1. ARCHITECTURE OVERVIEW

```
clawbot-line/
│
│  ┌─────────────────────────────────────────────────────────┐
│  │  LAYER A — The Actual LINE Bot (app/)                   │
│  │  main.py → FastAPI → app/api/webhook.py → ai_engine     │
│  │                     → app/api/health.py                 │
│  │  app/config.py (pydantic-settings, module-level init)   │
│  │  app/services/line_service.py  (global singleton)       │
│  │  app/services/openai_service.py (global singleton)      │
│  │  app/memory/store.py  (in-process dict, lost on restart)│
│  └─────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────┐
│  │  LAYER B — Dead Trading System (~3,000 lines, ~100 files)│
│  │  agents/ceo_*.py        (broken: undefined vars)        │
│  │  agents/finance_agents.py (broken: wrong API endpoint)  │
│  │  core/, market/, memory/, policies/, evolution/         │
│  │  world/, evaluation/, execution/, risk/, sizing/, etc.  │
│  │  adapters/, legacy/  (conflicting duplicate adapters)   │
│  └─────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────┐
│  │  ORPHANED / CONFLICTING                                 │
│  │  api.py       (standalone router, never registered)     │
│  │  routers/health.py  (duplicate of app/api/health.py)    │
│  │  worker.py    (infinite sleep loop, does nothing)       │
│  │  __init__.py  (at repo root — a Python antipattern)     │
│  └─────────────────────────────────────────────────────────┘
```

The repo was originally a trading/investment simulation engine ("Phase 96", CEO agent council, genetic evolution of strategies). A LINE bot `app/` layer was bolted on top without removing the original system. These two systems share a repository but have no runtime connection. The trading code is dead weight that causes confusion, contains broken code, and inflates the apparent complexity of what is actually a simple chatbot.

---

## 2. ANTI-PATTERNS

### AP-1: Module-level settings instantiation (CRITICAL)
**File:** `app/config.py:17` — `settings = Settings()`  
**File:** `app/api/webhook.py:14` — `parser = WebhookParser(settings.line_channel_secret)`  
Pydantic-settings throws a `ValidationError` when required env vars are absent. This fires at **import time**, not at request time. Every module that imports from `app/` will crash the Python process during import if the environment is not configured. This makes local development without a `.env` file impossible, breaks all unit tests, and makes Docker builds fragile. The parser being module-level means the LINE secret is resolved at import — you cannot rotate the secret without restarting the process, and you cannot test the webhook handler in isolation.

### AP-2: Global mutable singletons without thread safety
**File:** `app/services/line_service.py:10-11` — `_api_client`, `_messaging_api` globals  
**File:** `app/services/openai_service.py:14` — `_client` global  
These are initialised lazily with no lock. Under concurrent requests, two coroutines can enter the `if _messaging_api is None:` branch simultaneously and create duplicate clients. In asyncio this is less dangerous than in threads, but the pattern is still wrong and will cause confusion when adding tests.

### AP-3: In-process conversation memory
**File:** `app/memory/store.py` — `defaultdict(deque)`  
Conversation history is stored in a Python dict inside the process. Every restart wipes all conversations. Render free-tier instances restart frequently. If you ever run two uvicorn workers (`--workers 2`) each has its own isolated dict — user A's history may be on worker 1 while their next message lands on worker 2. This is a **silent correctness bug** at scale.

### AP-4: `max_history` ignores the config value
**File:** `app/memory/store.py:6` — `ConversationStore(max_history=10)` hardcoded  
**File:** `app/config.py` — `max_history_messages` field exists but is never read  
The config field is dead. The store always uses 10 messages regardless of what `MAX_HISTORY_MESSAGES` is set to in the environment.

### AP-5: No rate limiting despite installing slowapi
**File:** `requirements.txt` — `slowapi` is installed  
**Reality:** slowapi is never imported or configured anywhere in the codebase. The `/callback` endpoint is completely unprotected. Any actor who discovers the endpoint URL can flood it with requests and generate OpenAI API costs.

### AP-6: Health check does not check health
**File:** `app/api/health.py`  
The health endpoint only calls `get_client()` and `get_line_client()`, which are client constructor calls — they verify nothing about network reachability. The health check will return `"ok"` even if OpenAI is down, the LINE API is unreachable, or the secrets are wrong. Render uses this endpoint to route traffic; a false-positive health check means traffic gets sent to a broken instance.

### AP-7: LINE reply has no timeout protection
**File:** `app/api/webhook.py:31-45`  
LINE requires a 200 response within **5 seconds** of receiving a webhook or it marks the delivery as failed and retries. The webhook handler calls `get_ai_reply()` synchronously (within the request handler) before returning. OpenAI calls can easily exceed 5 seconds on first response or under load. There is no timeout, no background task, and no early acknowledgement. The result: LINE will retry the webhook (sending duplicate messages), and Render may log timeout errors.

### AP-8: Undefined variables in agent code that would crash at runtime
**File:** `agents/ceo_alpha.py:12-13` — `vote` and `stance` are used but never defined  
This code raises `NameError` if the `if` branch is ever entered. Syntax analysis passes (it's valid Python) but execution would crash. This is dead code but it's not isolated — if it were ever imported, the module itself imports fine but calling `ceo_alpha(...)` with a high-risk world state would blow up.

### AP-9: finance_agents.py calls a non-existent API endpoint
**File:** `agents/finance_agents.py:4` — `OPENAI_URL = "https://api.openai.com/v1/responses"`  
This endpoint does not exist in the OpenAI API. The real endpoint is `/v1/chat/completions`. Every call to `call_agent()` or `run_finance_swarm()` will receive a 404 and raise an HTTPError. This code has never successfully run against OpenAI.

### AP-10: Broken import namespaces throughout legacy code
**File:** `policies/base.py:2` — `from clawbot.core.decision import Decision`  
**File:** `adapters/legacy_phase96.py:3` — `from clawbot.core.decision import Decision`  
The package is not named `clawbot` — there is no `clawbot/` directory. These imports raise `ModuleNotFoundError` at runtime. The code was written for a differently-structured package that no longer exists.

### AP-11: Duplicate and conflicting health endpoint
**File:** `routers/health.py` and `app/api/health.py`  
Two separate health routers exist. `routers/health.py` is never registered in `main.py` but exists as an orphan. `api.py` is also never registered. The orphans could be accidentally imported and create confusion.

### AP-12: Root-level `__init__.py`
**File:** `./__init__.py`  
Having `__init__.py` at the repository root makes Python treat the repo root as a package. This can cause import shadowing issues and breaks tools that expect the root to be a plain directory (Docker, pytest discovery, certain import systems). It serves no purpose.

### AP-13: worker.py is a stub with no function
**File:** `worker.py`  
The entire worker is an infinite loop sleeping for 60 seconds and doing nothing. It is not connected to any queue, job scheduler, or async task system. Shipping this as "background task infrastructure" is misleading.

---

## 3. OVERENGINEERING vs UNDERENGINEERING

**Overengineering:**
- 100+ files of genetic algorithm trading simulation, CEO agent councils, portfolio sizing, compliance modules, and evolutionary strategy pruning — none of which connect to the LINE bot. This is not "future infrastructure"; it is dead code with a false appearance of sophistication.
- `world/market_probe.py` returns `random.uniform(60000, 70000)` as a "market snapshot" — elaborate infrastructure wrapping a random number generator.
- Two separate adapter classes (`adapters/legacy_phase96.py` and `legacy/phase96_adapter.py`) for the same thing, both broken, neither called.

**Underengineering:**
- No rate limiting (slowapi installed but unused).
- No request timeout for OpenAI calls (LINE's 5-second window is violated).
- No background task processing (the correct pattern for LINE bots is: acknowledge → queue → reply asynchronously).
- No persistence layer. In-memory conversation history is a prototype-only choice.
- No tests. Zero test files exist.
- No CI/CD pipeline.
- No structured error types; bare `Exception` is caught everywhere.
- Health check verifies nothing.

---

## 4. RUNTIME VERIFICATION

**Install:** Success — all dependencies install cleanly on Python 3.9+.

**Import test without .env:**
```
ERR app.services.openai_service: ValidationError (missing LINE_CHANNEL_SECRET, etc.)
ERR app.services.line_service:   ValidationError
ERR app.core.ai_engine:          ValidationError
ERR app.api.health:              ValidationError
ERR app.api.webhook:             ValidationError
```
Every module in `app/` crashes on import without env vars. This is ship-blocker issue #1.

**Syntax check:** All `.py` files parse successfully. No syntax errors.

**Runtime crash scenarios:**
1. Deploy to Render without setting env vars → process exits at startup
2. User sends message → OpenAI takes >5 seconds → LINE retries → duplicate messages sent
3. Deploy with multiple workers → user history is inconsistent across workers
4. Call `ceo_alpha()` with `global_risk="HIGH"` → `NameError: name 'vote' is not defined`
5. Call `run_finance_swarm()` → HTTP 404 from OpenAI (wrong endpoint)

---

## 5. AI SYSTEM DESIGN EVALUATION

**What's there:**
- Single-turn: user message → prepend system prompt → call OpenAI → send reply
- 10-message sliding window of conversation history stored in memory

**What's missing:**
- No streaming (LINE does not support streaming, but OpenAI streaming would still reduce perceived latency)
- No background task pattern (5-second LINE timeout not addressed)
- Conversation history lost on restart — users experience amnesia every time you deploy
- No context truncation strategy beyond the 10-message window (long messages can silently overflow the model's context)
- System prompt is a hardcoded one-liner: `"You are Clawbot, a helpful AI assistant. Be concise and friendly."` — no persona, no domain knowledge, no usage guidelines
- No token counting before API calls — a single very long user message could exhaust the model's context
- No user-specific configuration (language preference, bot mode, etc.)

**Redis/PostgreSQL/Vector DB recommendation:**
- **Redis**: Needed now. Replace in-process `ConversationStore` with Redis to survive restarts and support horizontal scaling. Cost on Render: ~$25/month.
- **PostgreSQL**: Needed at Month 1+. Store conversation logs, user metadata, usage metrics. Render provides managed Postgres at $7/month.
- **Vector DB (Pinecone / Qdrant)**: Not needed yet. Add when implementing RAG for domain-specific knowledge retrieval.

---

## 6. SCORES

### Architecture: 3/10
1. The repo mixes two unrelated systems with no clean boundary, making intent unclear to any new engineer.
2. Module-level settings instantiation is a fundamental structural error that breaks the entire development workflow.
3. The app layer (webhook → AI → reply) is the correct shape but has critical gaps (no background tasks, no persistence).
**To reach 10:** Delete or fully isolate the legacy trading code; implement background task processing; add persistence.

### Production Readiness: 2/10
1. Import fails without env vars — process will not start on a fresh deployment.
2. LINE 5-second timeout is not addressed — duplicate messages will be sent in production under any load.
3. No tests, no CI, no monitoring, no alerting.
**To reach 10:** Fix module-level init; implement background reply pattern; add tests and CI.

### Scalability: 2/10
1. In-memory conversation store is incompatible with horizontal scaling.
2. No rate limiting — a single bad actor can exhaust OpenAI quota.
3. No async queue for AI calls — every webhook is a blocking synchronous chain to OpenAI.
**To reach 10:** Redis for state; background queue (Celery or ARQ); rate limiting per user_id.

### Security: 4/10
1. LINE signature verification is correctly implemented using the official SDK.
2. But there is no rate limiting — the endpoint is open to abuse.
3. `user_id` is logged in error messages — minor PII concern under PDPA/GDPR.
**To reach 10:** Rate limiting per IP and per user_id; audit logging with PII redaction; dependency pinning.

### Code Quality: 4/10
1. The `app/` layer is clean, well-named, and readable.
2. The legacy layer contains broken code (undefined vars, wrong API endpoints) and should not exist in the same repo.
3. Zero test coverage.
**To reach 10:** Delete dead code; add tests; fix module-level init anti-pattern.

### AI System Design: 3/10
1. The pipeline is structurally sound (system prompt + history + user message → OpenAI).
2. No background processing violates LINE's 5-second contract.
3. In-memory history means the AI loses context on every restart — a fundamental correctness failure.
**To reach 10:** Background reply tasks; Redis-backed history; token budget management; better system prompt.

### DevOps / Infrastructure: 3/10
1. Dockerfile is correct and minimal.
2. render.yaml correctly references env var secrets without hardcoding.
3. No CI/CD, no health check that actually tests dependencies, no log aggregation strategy.
**To reach 10:** GitHub Actions CI; real health probe; structured JSON logging; alerting on error rate.

### Maintainability: 3/10
1. The `app/` layer is small and navigable.
2. The 100+ dead files create a misleading cognitive load — a new engineer cannot tell what is live code.
3. No documentation, no tests, no ADRs.
**To reach 10:** Delete dead code; write tests; document the architecture; add docstrings to public functions.

---

## 7. RECOMMENDED ARCHITECTURE

### Ideal Folder Structure
```
clawbot-line/
├── app/
│   ├── api/
│   │   ├── webhook.py       # POST /callback
│   │   └── health.py        # GET /health (real checks)
│   ├── core/
│   │   ├── ai_engine.py     # orchestrates OpenAI call
│   │   └── message_handler.py  # background reply logic
│   ├── services/
│   │   ├── line_service.py
│   │   └── openai_service.py
│   ├── memory/
│   │   └── store.py         # Redis-backed
│   └── config.py            # lazy-loaded settings
├── tests/
│   ├── test_webhook.py
│   ├── test_ai_engine.py
│   └── conftest.py
├── .github/workflows/ci.yml
├── main.py
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── docker-compose.yml       # local dev with Redis
└── render.yaml
```

### Recommended Stack
| Layer | Choice | Reason |
|---|---|---|
| Web framework | FastAPI | Already in use, correct choice |
| LINE SDK | line-bot-sdk v3 | Already in use, correct choice |
| AI provider | OpenAI (gpt-4o-mini) | Already in use; consider Anthropic Claude for cost/quality |
| Conversation state | Redis (upstash.com free tier) | Survives restarts, works across workers |
| Background tasks | FastAPI BackgroundTasks (short term) → ARQ (scale) | Non-blocking LINE replies |
| Database | PostgreSQL (Render managed) | Conversation logs, user metadata |
| Deployment | Render web service | Already configured |
| Monitoring | Sentry (error tracking) + Render metrics | Free tier available |
| CI/CD | GitHub Actions | Free for public repos |

### Background Reply Pattern (Critical Fix)
```python
@router.post("/callback")
async def callback(request: Request, background_tasks: BackgroundTasks, ...):
    body = await request.body()
    # Verify signature first — this is fast
    events = parser.parse(body.decode(), x_line_signature)
    # Acknowledge LINE immediately (within 5 seconds)
    for event in events:
        if isinstance(event, MessageEvent):
            background_tasks.add_task(handle_message, event)
    return {"status": "ok"}   # LINE gets 200 immediately

async def handle_message(event: MessageEvent):
    reply = await get_ai_reply(event.source.user_id, event.message.text)
    await reply_text(event.reply_token, reply)
```

### Lazy Config Loading (Critical Fix)
```python
# app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ...

@lru_cache
def get_settings() -> Settings:
    return Settings()
```
Modules import `get_settings` (the function), not `settings` (the instance). Settings are only parsed when first called at request time, not at import time.

### Database Architecture
- **Phase 1 (now):** Redis for conversation history (TTL 24h per user)
- **Phase 2 (Month 1):** PostgreSQL for user table, message logs, error logs
- **Phase 3 (Month 3+):** Vector store (Qdrant/Pinecone) if adding RAG over domain knowledge

### Scaling Strategy
1. Run single worker initially on Render
2. Move conversation state to Redis before adding second worker
3. Rate-limit at Cloudflare or via slowapi (per IP, per user_id)
4. Add Celery/ARQ when background tasks exceed FastAPI BackgroundTasks' reliability guarantees
5. Horizontal scale behind Render's load balancer once Redis is in place

### Monitoring Setup
```yaml
# Minimum viable observability
- Sentry SDK: capture all unhandled exceptions with user_id context (redacted)
- Structured JSON logging: {"level":"ERROR","user_id":"Uxxxx","event":"ai_failure"}
- Render health check: /health with real OpenAI ping (not just client init check)
- Uptime monitor: UptimeRobot or Better Uptime (free tier) on /health
```
