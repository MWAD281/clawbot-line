# TECHNICAL DEBT REGISTER — clawbot-line
**Date:** 2026-05-07  
**Total debt items:** 18

Priority: **P0** = ship blocker | **P1** = must fix before real users | **P2** = fix within Month 1 | **P3** = good to have  
Effort: **S** = <2h | **M** = 2–8h | **L** = 1–3 days | **XL** = 1+ week

---

## TD-01 — Module-level settings instantiation crashes imports
**Priority: P0 | Effort: M**  
**File:** `app/config.py:17`, `app/api/webhook.py:14`

`settings = Settings()` and `parser = WebhookParser(settings.line_channel_secret)` are executed at module import time. Any import of `app.*` without a `.env` file raises `ValidationError` and kills the process. This breaks local development, CI testing, and any Docker build step that imports Python modules.

**Fix:** Replace the module-level `settings` singleton with a `get_settings()` function decorated with `@lru_cache`. Move `parser` initialisation inside a dependency or function. Every callsite changes from `settings.x` to `get_settings().x`.

**Why it matters:** You currently cannot write a single unit test for the webhook handler without mocking all three env vars. CI will fail on any fresh runner.

---

## TD-02 — LINE 5-second timeout not addressed
**Priority: P0 | Effort: M**  
**File:** `app/api/webhook.py:31-45`

The webhook handler calls `get_ai_reply()` (which calls OpenAI) synchronously before returning a response. OpenAI p50 latency for gpt-4o-mini is ~1–3 seconds; p95 is >5 seconds under load. When the OpenAI call exceeds LINE's 5-second window, LINE marks the delivery as failed and retries — sending the same message again. The bot then processes it twice and sends duplicate replies.

**Fix:** Acknowledge LINE immediately with HTTP 200, then use `BackgroundTasks` (or a task queue) to process the AI call asynchronously.

---

## TD-03 — In-memory conversation history not suitable for production
**Priority: P0 | Effort: L**  
**File:** `app/memory/store.py`

Conversation history lives in a Python `defaultdict` inside the process. Consequences: (1) all history is lost on every deploy or restart; (2) multiple uvicorn workers each have isolated history — user A's context may be on a different worker for each request; (3) there is no TTL — the dict grows without bound for the process lifetime.

**Fix:** Replace with Redis. Upstash provides a free Redis tier. Use `user_id` as key, store JSON-serialised message list with a 24-hour TTL.

---

## TD-04 — `max_history_messages` config is dead
**Priority: P1 | Effort: S**  
**File:** `app/memory/store.py:6`, `app/config.py:8`

`ConversationStore` is instantiated with `max_history=10` (hardcoded). The `MAX_HISTORY_MESSAGES` env var is parsed by pydantic-settings but never read by the store. The config field is pointless.

**Fix:** One line: `conversation_store = ConversationStore(max_history=get_settings().max_history_messages)`

---

## TD-05 — slowapi installed but never configured
**Priority: P1 | Effort: S**  
**File:** `requirements.txt`, `app/api/webhook.py`

`slowapi` appears in requirements and is installed. It is not imported or applied anywhere. There is no rate limiting on any endpoint. The `/callback` endpoint can be flooded.

**Fix:** Add `Limiter` to the FastAPI app and apply `@limiter.limit("60/minute")` to the webhook endpoint.

---

## TD-06 — Health check is a stub
**Priority: P1 | Effort: M**  
**File:** `app/api/health.py`

`get_client()` and `get_line_client()` only initialise client objects — they do not make network calls. The health check returns `"ok"` regardless of whether OpenAI or LINE APIs are reachable. Render routes traffic based on this check.

**Fix:** Make the health check actually probe dependencies. For OpenAI: call `client.models.list()` with a short timeout. For LINE: call a lightweight messaging API endpoint. Cache the result for 30 seconds to avoid hammering APIs.

---

## TD-07 — 100+ files of dead trading system code
**Priority: P1 | Effort: M**  
**Files:** `agents/`, `core/` (trading), `market/`, `memory/` (trading), `policies/`, `evaluation/`, `execution/`, `risk/`, `sizing/`, `world/`, `human/`, `analysis/`, `legacy/` (large parts), `adapters/`

These files are not imported by any live code path in the current application. They create noise that makes the repository appear complex when it is not. They also contain broken code (see TD-08, TD-09) that will mislead anyone who tries to reuse it.

**Fix:** Delete or move to a separate archive branch. If you want to keep the trading system, it belongs in a separate repository.

---

## TD-08 — `agents/ceo_alpha.py` crashes at runtime
**Priority: P1 | Effort: S**  
**File:** `agents/ceo_alpha.py:12-13`

`vote` and `stance` are used in the return dict but are never assigned. `NameError` raised when `global_risk` is `"HIGH"` or `"LATENT_SYSTEMIC_RISK"`. Syntax is valid so this was never caught by linting.

**Fix:** Either delete the file or add `vote = "RISK_OFF"` and `stance = "DEFENSIVE"` before the return.

---

## TD-09 — `agents/finance_agents.py` calls non-existent API endpoint
**Priority: P1 | Effort: S**  
**File:** `agents/finance_agents.py:4`

`OPENAI_URL = "https://api.openai.com/v1/responses"` does not exist. The chat completions endpoint is `/v1/chat/completions`. Every call returns HTTP 404. This code has never worked.

**Fix:** Delete the file (it is dead code) or fix the endpoint URL and update the payload shape to match the chat completions API.

---

## TD-10 — Broken import namespaces in policies/ and adapters/
**Priority: P1 | Effort: S**  
**Files:** `policies/base.py:2`, `adapters/legacy_phase96.py:3`

Both files import from `clawbot.core.decision`. No such package exists. These are `ModuleNotFoundError` at import time.

**Fix:** Delete these files (they are dead code). If needed, fix the import to `from core.decision import Decision`.

---

## TD-11 — Zero test coverage
**Priority: P1 | Effort: XL**  
**Files:** none (no test files exist)

There are no unit tests, integration tests, or end-to-end tests. No test configuration (`pytest.ini`, `conftest.py`). This means every change is a manual deploy-and-click cycle. There is no way to verify signature verification logic, error fallback behaviour, or conversation history management without sending real LINE messages.

**Minimum to implement:**
- `tests/test_webhook.py` — test signature verification, valid message handling, fallback message on AI failure
- `tests/test_ai_engine.py` — test history management, fallback return on exception
- `tests/test_config.py` — test settings validation
- `conftest.py` — mock env vars and OpenAI client

---

## TD-12 — Unpinned dependencies
**Priority: P2 | Effort: S**  
**File:** `requirements.txt`

All dependencies are either unpinned or only minimum-version-pinned. A `pip install` six months from now may produce a different environment. FastAPI, pydantic-settings, and line-bot-sdk have all had breaking changes between minor versions.

**Fix:** Generate a locked `requirements.txt` using `pip-compile` from `requirements.in`. Commit both files. Run `pip-compile --upgrade` deliberately, not on every install.

---

## TD-13 — `worker.py` is a fiction
**Priority: P2 | Effort: S**  
**File:** `worker.py`

The background worker is an infinite `asyncio.sleep(60)` loop. It performs no work. It exists as scaffolding but shipping it creates the impression of a background processing system that does not exist.

**Fix:** Either delete `worker.py` and remove it from documentation, or replace it with a real background task (e.g., periodically cleaning up expired conversation history, or sending daily digests if that feature is planned).

---

## TD-14 — Root-level `__init__.py`
**Priority: P2 | Effort: S**  
**File:** `./__init__.py`

An empty `__init__.py` at the repository root makes Python treat the entire repo as a package. This can shadow imports and confuse tools. It has no purpose.

**Fix:** Delete it.

---

## TD-15 — Duplicate and orphaned routers
**Priority: P2 | Effort: S**  
**Files:** `routers/health.py`, `api.py`, `world/routes.py`

Three router files that are never registered in `main.py`. `routers/health.py` is a minimal health router superseded by `app/api/health.py`. `api.py` is a market snapshot router. `world/routes.py` calls `evolve_agents()` and `get_judgment()` which are part of the dead trading system. All three are dead code.

**Fix:** Delete all three.

---

## TD-16 — `memory/ceo_memory.py` creates files on disk in a container
**Priority: P2 | Effort: S**  
**File:** `memory/ceo_memory.py:12-13` — `BASE_DIR = Path("memory_store")` / `BASE_DIR.mkdir(exist_ok=True)`

This file (part of the dead trading system) creates a directory at startup relative to the working directory. In a container, this writes to the ephemeral container filesystem and is lost on restart. More importantly, in the live app this file is not called — but if it ever were imported, it would silently create a `memory_store/` directory that is not in `.gitignore`.

**Fix:** Delete this file as part of cleaning the trading system dead code.

---

## TD-17 — No structured logging format
**Priority: P2 | Effort: M**  
**File:** `main.py:8-11`

Logging is configured with a plain text format. In production, logs should be structured JSON so they can be queried, filtered, and indexed by log aggregation tools (Datadog, Papertrail, Render's log viewer). Plain text logs cannot be reliably parsed for error rate monitoring.

**Fix:** Add `python-json-logger` and configure a `JsonFormatter` in the logging setup.

---

## TD-18 — No CI/CD pipeline
**Priority: P2 | Effort: L**  
**File:** (missing `.github/workflows/`)

There is no automated test, lint, or build pipeline. Every push to `main` is deployed to Render without any verification. A push with a syntax error or a broken import will deploy and fail silently (or noisily, in production).

**Fix:** Create `.github/workflows/ci.yml` that runs `pip install`, `pytest`, and `ruff` on every pull request and push to `main`. Block merges if CI fails. Render can be configured to only deploy on CI green.
