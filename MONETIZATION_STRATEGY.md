# Monetisation Strategy — Clawbot LINE Bot

## Revenue Model Options

### Option 1: Freemium Consumer SaaS (Fastest to revenue)

**How it works:** Free tier (50 msg/day) → Paid tier (unlimited, premium model).

**Implementation delta from current codebase:**
- Stripe or PromptPay webhook → flip a Redis flag per user → raise/remove `daily_message_limit`
- Upgrade prompt when user hits limit (already triggered — just add a payment link)

**Thai market pricing:** ฿99–199/month ($3–6). At 1,000 paying users = ฿100–200k/month (~$3–6k MRR).

**Time to first revenue:** 2–4 weeks.

**Risk:** Consumer LINE bots have poor discoverability. Requires LINE OA marketing spend.

---

### Option 2: B2B White-Label Platform (Highest ceiling)

**How it works:** Sell to Thai SMEs (restaurants, clinics, salons) a branded LINE OA bot pre-configured for their domain (booking, FAQ, order tracking).

**Implementation delta:**
- Multi-tenant architecture: per-OA channel secret + token, per-OA system prompt stored in DB
- Admin dashboard: configure persona, knowledge base (RAG), working hours, escalation
- Monthly SaaS fee: ฿1,500–5,000/month ($45–150) per business

**Thai market sizing:** ~600k registered LINE OA accounts in Thailand; even 0.1% penetration = 600 customers = ฿900k–3M/month.

**Time to first revenue:** 6–10 weeks (needs multi-tenant + simple admin UI).

**Risk:** Sales cycle. SMEs need hand-holding and local Thai support.

---

### Option 3: Token Top-Up / Pay-Per-Use (Lowest friction)

**How it works:** Users buy message packs (e.g., 500 messages for ฿49). No subscription friction.

**Implementation delta:**
- Payment via LINE Pay or PromptPay QR
- Credit balance stored per user in Redis/PostgreSQL
- Decrement on each message; prompt to top up at 0

**Advantage:** Matches Thai consumer behaviour (prepaid culture). No recurring billing complexity.

**Time to first revenue:** 3–5 weeks.

---

## Recommended Path

**Phase 1 (Now → Week 4):** Freemium with daily limit + upgrade prompt  
The limit check is already implemented. Add a PromptPay QR payment link when the user hits the wall. Manual fulfilment initially (user screenshots payment → you flip a flag in Redis). Ugly but proves willingness to pay before building automation.

**Phase 2 (Week 5–10):** B2B pilot  
Approach 3–5 Thai SMEs (restaurants are the easiest vertical — they already use LINE OA). Offer free setup, charge ฿1,500/month. Use the revenue to fund Phase 3.

**Phase 3 (Month 3+):** Scale B2B with self-serve onboarding + RAG knowledge base.

---

## Unit Economics at Scale

| Metric | Conservative | Optimistic |
|--------|-------------|-----------|
| Monthly messages per paid user | 300 | 1,000 |
| OpenAI cost per message (gpt-4o-mini) | $0.001 | $0.001 |
| OpenAI cost per user/month | $0.30 | $1.00 |
| Revenue per user/month (B2C) | $3 | $6 |
| Gross margin | 90% | 83% |
| Revenue per SME/month (B2B) | $45 | $150 |
| OpenAI cost per SME/month | $5 | $20 |
| B2B gross margin | 89% | 87% |

LLM costs are not the constraint. Distribution and churn are.

---

## What To Build Next For Monetisation

1. **PostgreSQL user table** — store `user_id`, `tier`, `credits`, `created_at`. Needed for payment.
2. **Payment webhook handler** — PromptPay/Stripe → credit top-up.
3. **Upgrade prompt** — triggered by the daily-limit message already implemented.
4. **Admin stats endpoint** — `/admin/stats?token=X` showing DAU, total messages, revenue. Needed to operate the business.
