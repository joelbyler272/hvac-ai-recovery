# CallHook Production Deployment Guide

## Architecture

```
                    Vercel (Frontend)
                         |
Twilio ──► Railway (API) ──► Supabase (DB + Auth)
                |
          Railway (Worker + Beat) ──► Redis
```

Three Railway services, one Vercel app, one Supabase project.

---

## Step 1: Supabase Production Project

1. Go to [supabase.com](https://supabase.com) → New Project
2. Name: `callhook-prod`, Region: closest to your users
3. Save the generated database password
4. Once created, go to **Settings → API** and copy:
   - Project URL → `SUPABASE_URL`
   - `anon` key → `SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY`
5. Go to **Settings → Database → Connection string → Session Pooler**:
   - Copy the URI → `DATABASE_URL`
   - Use **Session mode** (port 5432), NOT Transaction mode
6. Run the SQL scripts in order:
   ```
   supabase/001_rls_policies.sql
   supabase/002_realtime.sql
   supabase/003_auth_triggers.sql
   supabase/004_indexes.sql
   supabase/005_functions.sql
   supabase/006_seed_dev.sql  (optional, for test data)
   ```
7. Run Alembic migrations:
   ```bash
   cd backend
   DATABASE_URL="your-prod-url" alembic upgrade head
   ```

---

## Step 2: Railway Backend

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
2. Select `joelbyler272/hvac-ai-recovery`
3. **Create 3 services** from the same repo:

### Service 1: API (web)
- **Root Directory:** `backend`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/health`
- Generate a domain (e.g., `callhook-api.up.railway.app`)

### Service 2: Worker
- **Root Directory:** `backend`
- **Start Command:** `celery -A app.worker.tasks worker --loglevel=info --concurrency=2`
- No domain needed (no HTTP traffic)

### Service 3: Beat (scheduler)
- **Root Directory:** `backend`
- **Start Command:** `celery -A app.worker.tasks beat --loglevel=info`
- No domain needed

### Service 4: Redis
- Add Redis from Railway's plugin marketplace
- Copy the `REDIS_URL` it provides

### Environment Variables (shared across API + Worker + Beat)

Set these on all three backend services:

```
# Core
ENVIRONMENT=production
BASE_URL=https://callhook-api.up.railway.app
ALLOWED_ORIGINS=https://app.callhook.com
ADMIN_API_KEY=<generate a strong random key>
DEBUG=false

# Supabase
SUPABASE_URL=<from step 1>
SUPABASE_ANON_KEY=<from step 1>
SUPABASE_SERVICE_ROLE_KEY=<from step 1>
DATABASE_URL=<from step 1, session pooler>

# Redis
REDIS_URL=<from Railway Redis plugin>

# Twilio
TWILIO_ACCOUNT_SID=<your Twilio SID>
TWILIO_AUTH_TOKEN=<your Twilio auth token>

# Vapi
VAPI_API_KEY=<your Vapi key>
VAPI_WEBHOOK_SECRET=<your Vapi webhook secret>

# OpenAI
OPENAI_API_KEY=<your OpenAI key>

# Resend
RESEND_API_KEY=<your Resend key>
EMAIL_FROM_ADDRESS=CallHook <notifications@yourdomain.com>

# Stripe
STRIPE_SECRET_KEY=<your Stripe secret key>
STRIPE_WEBHOOK_SECRET=<from Stripe webhook setup>

# Sentry
SENTRY_DSN=<your Sentry DSN>

# Business config
SUBSCRIPTION_COST=497.0
FOLLOW_UP_DELAY_MINUTES=120,1440
OWNER_NUDGE_DELAY_MINUTES=30
```

---

## Step 3: Vercel Frontend

1. Go to [vercel.com](https://vercel.com) → Import Git Repository
2. Select `joelbyler272/hvac-ai-recovery`
3. **Root Directory:** `frontend`
4. **Framework Preset:** Next.js (auto-detected)
5. **Environment Variables:**

```
NEXT_PUBLIC_SUPABASE_URL=<from step 1>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<from step 1>
NEXT_PUBLIC_API_URL=https://callhook-api.up.railway.app
NEXT_PUBLIC_SENTRY_DSN=<your Sentry DSN, client-safe>
```

6. Deploy. Vercel gives you a URL like `callhook-dashboard.vercel.app`
7. (Optional) Add custom domain: `app.callhook.com`

---

## Step 4: Twilio Webhook Configuration

1. Go to [Twilio Console](https://console.twilio.com) → Phone Numbers
2. For each CallHook Twilio number, set:
   - **Voice → A Call Comes In:** Webhook `https://callhook-api.up.railway.app/webhook/voice/incoming` (POST)
   - **Messaging → A Message Comes In:** Webhook `https://callhook-api.up.railway.app/webhook/sms/incoming` (POST)
   - **Messaging → Status Callback:** `https://callhook-api.up.railway.app/webhook/sms/status` (POST)

### Test it:
```bash
curl https://callhook-api.up.railway.app/health
# Should return: {"status":"healthy","version":"1.0.0"}
```

---

## Step 5: Stripe Webhook

1. Go to [Stripe Dashboard](https://dashboard.stripe.com) → Developers → Webhooks
2. Add endpoint: `https://callhook-api.up.railway.app/webhook/stripe/`
3. Select events:
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.deleted`
   - `customer.subscription.paused`
   - `customer.subscription.resumed`
4. Copy the webhook signing secret → `STRIPE_WEBHOOK_SECRET` env var

---

## Step 6: Sentry Error Tracking

1. Go to [sentry.io](https://sentry.io) → Create Project
2. Create **two projects**:
   - `callhook-api` (Python / FastAPI)
   - `callhook-dashboard` (Next.js)
3. Copy each project's DSN
4. Set `SENTRY_DSN` on Railway (backend)
5. Set `NEXT_PUBLIC_SENTRY_DSN` on Vercel (frontend)

---

## Step 7: A2P 10DLC Registration (Twilio)

Required for reliable SMS delivery. Without it, 30-80% of messages get carrier-filtered.

1. Go to Twilio Console → Messaging → Trust Hub → A2P Brand Registration
2. Register your brand ($4 one-time):
   - Business name, EIN, address, website
3. Create a Campaign ($15/month):
   - Use case: "Customer Care" or "Mixed"
   - Sample messages: include opt-out language
4. Assign your Twilio number(s) to the campaign
5. Wait for approval (1-5 business days)

---

## Step 8: Vapi Webhook Configuration

1. Go to [Vapi Dashboard](https://dashboard.vapi.ai)
2. Settings → Webhooks → Server URL: `https://callhook-api.up.railway.app/webhook/vapi/call-ended`
3. Set a webhook secret → `VAPI_WEBHOOK_SECRET` env var

---

## Verification Checklist

After deployment, verify each piece:

- [ ] `curl https://your-api.up.railway.app/health` returns healthy
- [ ] Frontend loads at your Vercel URL
- [ ] Can sign in via Supabase Auth
- [ ] Dashboard shows (empty) stats
- [ ] Call your Twilio number → phone rings → if missed → voice AI answers
- [ ] SMS to Twilio number → AI responds
- [ ] Check Sentry for any errors
- [ ] Check Railway logs for startup errors
- [ ] Stripe test webhook fires and reaches your endpoint

---

## Custom Domain (Optional)

### API: `api.callhook.com`
- Railway → Service → Settings → Custom Domain → add `api.callhook.com`
- Add CNAME record in your DNS: `api.callhook.com → <railway-provided-target>`
- Update `BASE_URL` env var to `https://api.callhook.com`
- Update Twilio webhook URLs to use the new domain

### Frontend: `app.callhook.com`
- Vercel → Project → Settings → Domains → add `app.callhook.com`
- Add CNAME record in your DNS: `app.callhook.com → cname.vercel-dns.com`
- Update `ALLOWED_ORIGINS` on Railway to `https://app.callhook.com`
