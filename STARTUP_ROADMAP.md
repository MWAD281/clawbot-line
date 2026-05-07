# Startup Roadmap — Clawbot

## North Star Metric
**Monthly Recurring Revenue (MRR)** — everything is secondary to finding users who pay.

---

## Phase 0: Foundation (Done ✓)
- [x] FastAPI + LINE Bot SDK v3
- [x] OpenAI integration with async history
- [x] Rate limiting, signature verification, error handling
- [x] CI/CD pipeline (GitHub Actions → Render)
- [x] Structured JSON logging
- [x] Docker + docker-compose
- [x] Daily message limits (usage controls)
- [x] Optional Sentry error monitoring

---

## Phase 1: First Paying User (Weeks 1–4)
**Goal:** ฿1 of real revenue. Proves willingness to pay.

### Tasks
- [ ] Add upgrade prompt when user hits daily limit (include PromptPay QR or LINE Pay link)
- [ ] Manual payment fulfilment: user sends screenshot → admin flips Redis key
- [ ] PostgreSQL table: `users(line_user_id, tier, credits, created_at)`
- [ ] Basic admin endpoint: `/admin/stats` with message counts and user counts
- [ ] Deploy UptimeRobot ping to keep Render service warm

### Success metric
5 paying users @ ฿99/month = ฿495 MRR

---

## Phase 2: Product–Market Fit Signal (Months 1–3)
**Goal:** Find a vertical where retention > 40% at day-30.

### Vertical experiments (run in parallel, 2 weeks each)
1. **Thai customer service bot** — for small restaurants / cafes
2. **Language learning** — English ↔ Thai practice partner
3. **Personal productivity** — reminders, Q&A, note-taking via LINE

### Tasks
- [ ] Multi-tenant architecture: per-OA `channel_secret` + `channel_token` + system prompt
- [ ] RAG: per-tenant knowledge base (PDF/text upload → chunked embeddings → pgvector)
- [ ] PostgreSQL migration with Alembic
- [ ] Token budget management (prevent runaway costs per user)
- [ ] Payment automation: PromptPay webhook via Omise or 2C2P

### Success metric
50 paying users, one vertical with day-30 retention ≥ 40%

---

## Phase 3: Revenue & Infrastructure (Months 3–6)
**Goal:** ฿50k MRR ($1,500). Enough to cover costs and validate scale.

### Tasks
- [ ] Self-serve onboarding: web dashboard to configure bot, upload knowledge base, manage billing
- [ ] Multi-model support: fallback to Claude or Gemini if OpenAI is down; per-tier model selection
- [ ] Redis Streams or Celery for async job queue (decouple LINE webhook from AI call)
- [ ] Horizontal scaling: session affinity via Redis, multiple Render instances or Railway
- [ ] Sentry + Datadog/Grafana for production observability
- [ ] OpenTelemetry tracing for LLM calls

### Success metric
฿50k MRR, <0.1% error rate, p99 latency <2s

---

## Phase 4: Moat & Scale (Month 6+)
**Goal:** Defensibility. Build what incumbents can't copy easily.

### Tasks
- [ ] Thai-language fine-tuned model or domain-specific RAG corpus
- [ ] LINE Flex Message UI (rich cards, buttons, carousels) for B2B clients
- [ ] Webhook event store + replay (audit trail, analytics, re-engagement)
- [ ] Agent tools: web search, calculator, appointment booking via Google Calendar API
- [ ] Partner programme: let agencies resell white-label bots

### Success metric
฿200k MRR ($6k), 3+ enterprise accounts, partner network active

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OpenAI price increase | Medium | High | Multi-model abstraction layer |
| LINE API breaking change | Low | High | Pin SDK version; monitor changelog |
| Render free-tier removal | High | Medium | Already on paid tier via deploy hook |
| Thai competitor with better distribution | Medium | High | Speed + vertical depth |
| Render cold starts churn users | High | Medium | UptimeRobot + health-check ping |

---

## Fundraising Gate

Do NOT raise external capital until:
1. ฿50k MRR with organic growth
2. One vertical with measurable retention
3. Automation of at least the payment flow

Before that threshold, external money is a distraction. The product needs signal, not scale.
