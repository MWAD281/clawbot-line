# ENGINEERING ROADMAP — clawbot-line
**Date:** 2026-05-07  
**Context:** This roadmap assumes the goal is a production-quality LINE chatbot backed by OpenAI. Items are ordered by impact/urgency. Each item references the TECH_DEBT or SECURITY_REVIEW entry it closes.

---

## PHASE 1 — Immediate (Week 1–2): Ship Blockers
*These must be fixed before any real user traffic. Deploy with these open and you will have duplicate messages, broken CI, and unbounded OpenAI costs.*

### 1.1 Fix module-level settings crash
**Refs:** TD-01  
**What:** Replace `settings = Settings()` at module level with `@lru_cache get_settings()`. Move `parser = WebhookParser(...)` inside a `Depends()` or lazy function.  
**Why:** The app crashes on import without env vars. You cannot write tests. Fresh deployments fail if Render doesn't inject the env vars before the Python process starts.  
**Effort:** M (3–4h) — touches ~6 files  
**Expected outcome:** All modules importable without env vars; tests can mock settings cleanly.

### 1.2 Implement background task pattern for LINE replies
**Refs:** TD-02, SEC-04  
**What:** In `webhook.py`, after signature verification, hand message events to `BackgroundTasks.add_task()` and return `{"status":"ok"}` immediately. Move `get_ai_reply()` + `reply_text()` into the background task function.  
**Why:** LINE requires HTTP 200 within 5 seconds or it retries the delivery, causing duplicate messages. OpenAI calls routinely exceed 5s under normal load.  
**Effort:** M (2–3h)  
**Expected outcome:** LINE delivers every message exactly once; no duplicate replies.

### 1.3 Add rate limiting
**Refs:** TD-05, SEC-02  
**What:** Configure `slowapi.Limiter` on the app. Apply `@limiter.limit("60/minute")` per IP on `/callback`. Add a per-`user_id` limit of 30/minute once the background task pattern is in place.  
**Why:** Zero cost protection against accidental loops or deliberate flooding. A single user in a loop could exhaust your OpenAI quota in minutes.  
**Effort:** S (1–2h)  
**Expected outcome:** Individual users and IPs are throttled; OpenAI cost is bounded.

### 1.4 Delete all dead trading system code
**Refs:** TD-07, TD-08, TD-09, TD-10, TD-14, TD-15, TD-16  
**What:** Delete: `agents/`, `core/` (the trading one), `market/`, `memory/` (trading), `policies/`, `evaluation/`, `execution/`, `risk/`, `sizing/`, `world/`, `human/`, `analysis/`, `adapters/`, orphan routers (`api.py`, `routers/`, `world/routes.py`), `__init__.py` at root, `worker.py` (stub).  
**Why:** These 100+ files contain broken code, confuse every new engineer, and make the repository appear to be something it is not. They provide zero value to the LINE bot.  
**Effort:** S (1h to delete + 1h to verify nothing breaks)  
**Expected outcome:** Repository shrinks from ~3,500 lines across 130 files to ~300 lines across 15 files. Architecture is legible in 5 minutes.

### 1.5 Fix `max_history_messages` config wiring
**Refs:** TD-04  
**What:** One-line fix in `app/memory/store.py` — pass `get_settings().max_history_messages` to `ConversationStore`.  
**Effort:** S (15 min)  
**Expected outcome:** `MAX_HISTORY_MESSAGES` env var controls conversation window as documented.

---

## PHASE 2 — Short Term (Month 1): Production Stability
*These items make the application reliable and observable for real users.*

### 2.1 Add Redis-backed conversation history
**Refs:** TD-03  
**What:** Replace `app/memory/store.py`'s in-process `defaultdict` with a Redis client (Upstash free tier or Render Redis). Keys: `conv:{user_id}`, value: JSON list of messages, TTL: 24h. Wrap with the same `ConversationStore` interface so no other code changes.  
**Why:** Every deploy or worker restart currently wipes all conversation history. Users re-introduce themselves after every deployment. Multi-worker setups have inconsistent history across workers.  
**Effort:** L (1–2 days including infra setup)  
**Expected outcome:** Conversation history survives restarts and scales across workers.

### 2.2 Write minimum viable test suite
**Refs:** TD-11  
**What:** 
- `tests/test_webhook.py`: test valid message, invalid signature (expects 400), missing signature header, fallback message on AI failure
- `tests/test_ai_engine.py`: test history prepend, fallback return on exception, history not stored on failure
- `tests/conftest.py`: mock `get_settings()`, mock `AsyncOpenAI`, mock LINE client
**Why:** Without tests, every code change requires a manual LINE message to verify. Regressions go undetected until users report them.  
**Effort:** L (2–3 days to write good tests)  
**Expected outcome:** `pytest` green on every PR; regressions caught before deploy.

### 2.3 Add CI/CD pipeline
**Refs:** TD-18  
**What:** `.github/workflows/ci.yml` — on every PR and push to main: `pip install -r requirements-dev.txt`, `ruff check .`, `pytest --cov=app`. Block merges if any step fails. Configure Render to deploy only on CI green (Render supports this via deploy hooks).  
**Effort:** M (3–4h)  
**Expected outcome:** No broken code reaches production; deploy confidence increases.

### 2.4 Fix health check to actually probe dependencies
**Refs:** TD-06  
**What:** In `app/api/health.py`, make a real network call to verify OpenAI and LINE are reachable. Cache result for 30s. Return HTTP 503 (not 200) when degraded — Render's health check will stop routing traffic.  
**Effort:** M (2–3h)  
**Expected outcome:** Render correctly pulls bad instances from rotation; on-call alerts fire when OpenAI is down.

### 2.5 Add structured JSON logging
**Refs:** TD-17  
**What:** Install `python-json-logger`. Replace `logging.basicConfig(format=...)` with a `JsonFormatter`. Every log line becomes `{"ts":"...","level":"ERROR","logger":"app.api.webhook","user_id_prefix":"Uabc...","event":"ai_failure"}`.  
**Why:** Render's log viewer and any downstream aggregator (Datadog, Papertrail) cannot parse plain-text logs reliably.  
**Effort:** M (2h)  
**Expected outcome:** Searchable, filterable logs; can alert on error rate from log volume.

### 2.6 Redact PII from logs
**Refs:** SEC-03  
**What:** Replace `user_id` in all log statements with `user_id[:8]+"..."`. Ensure exception messages do not include user message content.  
**Effort:** S (30 min)  
**Expected outcome:** Logs comply with PDPA/GDPR minimisation principle.

### 2.7 Pin dependency versions
**Refs:** TD-12  
**What:** Run `pip-compile requirements.in > requirements.txt`. Commit both files. Add Dependabot alerts for security updates.  
**Effort:** S (1h)  
**Expected outcome:** Reproducible builds; no surprise breaking changes from unpinned deps.

---

## PHASE 3 — Mid Term (Month 2–3): Scale and Reliability
*These items prepare the system for growth in users and features.*

### 3.1 Add Sentry error monitoring
**What:** Install `sentry-sdk[fastapi]`. Initialise in `main.py` with your Sentry DSN. Tag events with `user_id` (hashed) and `app_env`. Set up Slack alert for error rate > 5/minute.  
**Why:** Currently you have no visibility into production errors unless a user complains. Sentry gives you stack traces, breadcrumbs, and alert routing for free on the hobby tier.  
**Effort:** S (2h)  
**Expected outcome:** Know about errors before users report them.

### 3.2 Improve system prompt
**What:** Expand the system prompt from one line to a proper persona document. Include: bot purpose, language preference (Thai/English), topic boundaries, refusal instructions for financial advice, prompt injection resistance, response format guidelines.  
**Why:** The current system prompt provides zero guidance for anything beyond "be helpful". Users can easily extract, manipulate, or confuse the bot.  
**Effort:** M (several hours of prompt engineering and testing)  
**Expected outcome:** Consistent bot behaviour; reduced prompt injection risk; better user experience.

### 3.3 Add PostgreSQL for user data and message logs
**What:** Add a Render-managed PostgreSQL instance. Schema: `users(user_id, created_at, language_pref)`, `messages(id, user_id, role, content, created_at, token_count)`, `errors(id, user_id, error_type, created_at)`. Use SQLAlchemy async.  
**Why:** Without a database you cannot: analyse usage, debug individual user issues, implement user preferences, monitor AI quality, or report costs.  
**Effort:** XL (3–5 days including schema design and migration setup)  
**Expected outcome:** Full audit trail; usage analytics; foundation for user-specific features.

### 3.4 Implement token budget management
**What:** Before calling OpenAI, count the tokens in the messages array using `tiktoken`. If the total exceeds 3,500 tokens (leaving ~500 for the response), truncate older history. Log the truncation.  
**Why:** Long conversations silently exceed the model's context window. OpenAI will return an error or truncate the context unpredictably.  
**Effort:** M (3–4h)  
**Expected outcome:** No context overflow errors; predictable AI behaviour for long conversations.

### 3.5 Replace FastAPI BackgroundTasks with ARQ task queue
**What:** When BackgroundTasks proves insufficient (tasks not completing reliably, no retry on failure, no dead letter queue), migrate to ARQ (async Redis Queue). Tasks become: `enqueue("handle_message", user_id, text, reply_token)`. Add a separate ARQ worker process.  
**Why:** FastAPI BackgroundTasks have no retry, no persistence across restarts, and no visibility. If the process restarts mid-task, the LINE reply is lost permanently.  
**Effort:** L (2 days)  
**Expected outcome:** Reliable message delivery with retry; observable task queue; no lost replies on deploy.

---

## PHASE 4 — Long Term (Month 4+): Ideal Architecture
*These items transform the bot from a simple chatbot into a robust, extensible AI assistant platform.*

### 4.1 Add domain-specific knowledge with RAG
**What:** Add a Vector DB (Qdrant self-hosted on Render, or Pinecone managed). Build an ingestion pipeline for domain documents (if the bot serves a specific knowledge domain). Add a retrieval step before the OpenAI call: embed user query → search top-k chunks → inject into context.  
**Why:** LLMs hallucinate facts. For any domain-specific bot (financial, product, support), grounding responses in authoritative documents dramatically reduces hallucination.  
**Effort:** XL (1–2 weeks)  
**Expected outcome:** Factually grounded responses; reduced hallucination; differentiated product.

### 4.2 Multi-agent pipeline (if finance features are revived)
**What:** If the original vision of a finance-oriented bot is pursued, rebuild the agent pipeline properly: use the OpenAI Assistants API or LangGraph for agent orchestration, not custom random-number generators and mock market data. Each agent (crypto, macro, sentiment) should call real data APIs. The synthesis agent should produce structured output, not free text.  
**Why:** The existing `finance_agents.py` calls a non-existent API endpoint and the market data is `random.uniform()`. If the product direction includes financial analysis, the entire pipeline needs to be built from scratch with real data.  
**Effort:** XL (2–4 weeks minimum)  
**Expected outcome:** Actual financial analysis capability; real market data; structured, auditable agent decisions.

### 4.3 Multi-language support and user preferences
**What:** Detect user language from message content (or explicit preference command). Store language preference per user in PostgreSQL. Route to language-specific system prompt variants. Support at minimum Thai and English.  
**Effort:** L (2–3 days)  
**Expected outcome:** Localised experience; reduced friction for Thai-language users.

### 4.4 Observability platform
**What:** Integrate OpenTelemetry. Export traces to Honeycomb or Grafana Cloud. Instrument: webhook receipt → background task start → OpenAI call latency → LINE reply sent. Create dashboards for: p50/p95 reply latency, OpenAI error rate, messages per day, cost per message.  
**Effort:** L (2–3 days)  
**Expected outcome:** Full visibility into production performance; data-driven optimisation; cost tracking.
