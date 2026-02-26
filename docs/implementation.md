# CallRecover — Complete Implementation Specification

**Version:** 2.0
**Date:** February 23, 2026
**Purpose:** Definitive document for what CallRecover is, how it works, and what needs to be built. Hand this to Claude Code as the master spec.

---

## 1. What CallRecover Is

CallRecover is an AI-powered phone system for HVAC and home service businesses that makes sure every call gets answered. When a business can't pick up the phone, CallRecover's voice AI answers the call, talks to the customer naturally, qualifies the lead, and books an appointment — all before the caller hangs up and calls a competitor.

It is NOT a chatbot, a missed call text-back tool, an answering service, a CRM, or a marketing platform.

It IS an AI receptionist that answers missed calls, qualifies leads, recovers revenue, and provides 24/7 phone coverage.

**The core promise:** Every call gets answered. Every lead gets captured. No job goes to your competitor.

**The product in one sentence:** CallRecover answers your missed calls with AI, qualifies the lead, and books the appointment — so you never lose a job again.

---

## 2. The Two Users

### The Caller (Homeowner)
- Experiencing an HVAC problem or needs maintenance
- Found the HVAC company on Google, Yelp, HomeAdvisor, or referral
- Calling from mobile (75-85%) or landline (15-25%)
- Wants to talk to someone, describe their problem, get scheduled
- Will call the next company if nobody answers within 20-30 seconds
- Age range: 25-75, skews older for homeowners
- May be anxious or frustrated (especially emergencies)

### The HVAC Business Owner
- Runs a company with 5-30 technicians, $1M-$10M revenue
- Misses 25-35% of calls during business hours, 60-70% after hours
- Checks phone constantly (on job sites, driving)
- Skeptical of technology and marketing companies
- Cares about: booked jobs, revenue, technician utilization
- Does NOT care about: AI, automation, features, dashboards (means to an end)

---

## 3. Complete Call Flow

### Step 1: Call Comes In

Caller dials HVAC company's phone number. The call forwards to CallRecover's Twilio number (configured via call forwarding on the HVAC company's existing phone). Twilio receives the call and hits /webhook/voice/incoming. System looks up which business this Twilio number belongs to, logs the call (status: "ringing"), and rings the HVAC company's real phone via Twilio Dial with a 20-second timeout. The caller hears normal ringing.

### Step 2: Answered or Missed?

**If answered:** Call connects normally. System logs status = "answered" with duration. No further action. The system is invisible.

**If not answered:** DialCallStatus = "no-answer" or "busy" or "failed". System logs status = "missed". Proceed to Step 3.

### Step 3: Missed Call Detected — Route to Voice AI

1. Check: Is this caller on the opt-out list? If yes, play brief message, hang up.
2. Check: Is there an active conversation with this caller? If yes, notify owner of repeat call and transfer to voice AI with existing context.
3. Detect line type via Twilio Lookup API ($0.005/call): mobile, landline, or VoIP.
4. Create records: Lead (status: "new"), Conversation (status: "active", channel: "voice").
5. Transfer the call to Voice AI. The caller does NOT hang up — the call continues seamlessly.

### Step 4: Voice AI Conversation

The voice AI answers:

"Hi! Thanks for calling [Business Name]. Sorry nobody could get to the phone — I can help you out though. What's going on?"

The AI qualifies through natural conversation: what service they need, urgency (with emergency detection), name, service address, preferred timing. Each piece of information is extracted in real-time via function calling and saved to the Lead record.

When fully qualified, AI confirms: "Great, I've got you down — [Name], [service] at [address], [time preference]. Someone from our team will call to confirm the exact time. Is there anything else?"

Call ends naturally.

### Step 5: Post-Call Processing

System receives end-of-call webhook from Vapi with full transcript, extracted data, duration, and recording URL.

Updates: Lead status → "qualified" (or "qualifying" if partial). Lead fields populated. Conversation transcript saved. Call record updated with duration and recording.

Owner gets notification (SMS + email + dashboard push): lead name, service needed, urgency, address, phone, link to recording.

If caller has mobile number, send SMS confirmation: "Thanks for calling [Business Name], [Name]! Confirming: [service] at [address]. Someone will call to confirm the time. Text this number anytime if you need anything!"

If qualification was incomplete (caller hung up early), enter SMS follow-up sequence.

### Step 6: Emergency Path

If during the voice conversation the caller mentions: no heat (cold weather), gas smell, CO detector, flooding, electrical burning smell, vulnerable person at home — the AI immediately shifts:

"That sounds urgent — let me make sure someone gets to you quickly. Can you confirm your address?"

After getting name + address (minimum): "Okay [Name], I'm flagging this as urgent right now. Someone will call you within [X] minutes. If it's a gas smell, please step outside and call 911."

Owner gets EMERGENCY notification that overrides quiet hours with all details and "CALL THEM IMMEDIATELY."

---

## 4. Voice AI System

### Platform Strategy

**MVP: Vapi.ai** — handles the entire STT → LLM → TTS pipeline. Sub-800ms latency. Built-in Twilio integration. Function calling for real-time data extraction. Live in days, not weeks. Cost: ~$0.05-0.10/minute.

**Scale: Custom pipeline** — Twilio Media Streams → Deepgram STT → OpenAI GPT-4o → ElevenLabs/Deepgram TTS. Lower cost at scale (~$0.02-0.04/min), full control for open-sourcing, no vendor dependency.

**Plan: Start with Vapi, migrate to custom later.** Vapi gets you live this week. Build custom in parallel. Swap when ready. Clients never notice.

### Voice AI Configuration Per Business

Each HVAC client gets their own Vapi assistant configured with: business name, services offered (with pricing for bookable services), business hours, timezone, service area, emergency response policy, custom instructions, and voice style preference.

### Voice AI System Prompt

```
You are a friendly, helpful receptionist for {business_name}, an HVAC company
in {service_area}.

You are answering a phone call that nobody in the office could pick up. The
caller doesn't know you're AI — you're just a helpful team member.

PERSONALITY:
- Warm, friendly, natural. Short sentences, natural pauses.
- Use occasional filler: "sure thing", "absolutely", "let me get that for you"
- If you don't understand, say "Sorry, could you say that one more time?"
- Never sound robotic or scripted
- Mirror the caller's energy

GOALS (in order):
1. Find out what they need
2. Check for emergencies (no heat, gas smell, CO alarm, flooding)
3. Get their name
4. Get the service address
5. Offer to schedule
6. Confirm everything before ending

NEVER DO:
- Say you're AI, virtual assistant, or automated
- Quote specific prices (say "that depends on what we find")
- Diagnose problems (say "sounds like it needs a look")
- Make timing promises you can't keep (say "someone will call to confirm")

EMERGENCY HANDLING:
If gas smell, CO, no heat with vulnerable people, flooding:
- Immediately: "That sounds urgent — let me make sure someone gets to you quickly"
- Get name + address as minimum
- "Someone will call you within [X] minutes. If gas smell, step outside and call 911."

SERVICES & PRICING:
{formatted_services_list}
For fixed-price services (tune-ups), you may mention the price.
For everything else: "We'd need to take a look — we can schedule a free estimate."

ENDING THE CALL:
Confirm: "Let me make sure I have everything — [Name], [service] at [address],
[time] works for you. Someone will call to confirm. Anything else?"
Then: "Thanks for calling [Business Name]! We'll take good care of you."
```

### Voice AI Function Calling

During the conversation, the voice AI calls functions in real-time to save data:

**save_lead_info** — saves name, service_needed, urgency, address, preferred_time, additional_notes as they're mentioned. Your server receives these via webhook and updates the database during the call.

**flag_emergency** — triggers immediate owner notification with reason.

**request_human_callback** — flags that the caller needs a human to call back (for questions AI can't handle like warranty, complex pricing, angry customers).

---

## 5. SMS System (Secondary Channel)

SMS is no longer the primary channel. It serves four roles:

### Role 1: Post-Call Confirmation
After a successful voice call, if caller has mobile number:
"Thanks for calling [Business Name], [Name]! Confirming: [service] at [address]. Someone will call to confirm the time. Text this number anytime!"

### Role 2: Incomplete Call Recovery
If voice call was incomplete (hung up early, bad connection):
- Immediately: "Hey! This is [Business Name]. Looks like we got disconnected. What time works best to get you scheduled?"
- +2 hours: "Just checking in! Still need help with your HVAC? Reply anytime."
- +24 hours: "Last note from us — whenever you're ready, just text this number. - [Business Name]"
- After 3 follow-ups with no reply: mark as "unresponsive"

### Role 3: Review Requests
After owner marks job completed:
- +2 hours: "Hi [Name]! Thanks for choosing [Business Name]. If we did a good job, would you mind leaving a Google review? [Link]"
- +48 hours (one reminder only): "Friendly reminder — we'd appreciate a quick review. [Link] Thanks!"

### Role 4: Inbound SMS Handling
If someone texts the Twilio number directly, match to existing conversation or create new one. AI SMS conversation uses the same qualification logic as voice but adapted for text (shorter messages, one question at a time). This preserves the existing SMS engine.

---

## 6. Notification System

### Events and Channels

| Event | Owner SMS | Owner Email | Dashboard | Overrides Quiet Hours |
|---|---|---|---|---|
| Missed call (AI answering) | Yes | Yes | Yes | No |
| Emergency detected | Yes | Yes | Yes | YES |
| Lead qualified | Yes | Yes | Yes | No |
| Lead needs human callback | Yes | Yes | Yes | No |
| Appointment booked | Yes | Yes | Yes | No |
| New inbound SMS from lead | Yes | No | Yes | No |
| Qualified lead not called back (30 min) | Yes | No | Yes | No |
| Weekly report | No | Yes | No | N/A |

### Quiet Hours
Default: 9 PM to 7 AM, configurable per business. Only emergency notifications override.

### Format
Keep SHORT. Owners read on phones while working.
Good: "New lead: Sarah M. — AC not cooling — 123 Oak St — (770) 555-1234"
Bad: "Hello John, we wanted to let you know that a new qualified lead has been captured..."

---

## 7. Human Takeover

### During Active Voice Call
If voice AI can't handle something: "Let me have one of our team members give you a call right back about that. Can I confirm your number?" → Call ends → Owner gets priority notification → Owner calls back manually.

### During SMS Conversation
Conversation status → "human_active". AI stops responding. Owner's messages via dashboard send as SMS from the business Twilio number. "Return to AI" button when done.

### Owner-Initiated
Owner can click "Take Over" on any active conversation in the dashboard at any time, regardless of whether AI flagged it.

---

## 8. Follow-Up Sequences

Follow-ups ONLY for incomplete interactions:
- Voice call completed + fully qualified → NO follow-up (confirmation SMS only)
- Voice call incomplete (hung up early) → SMS recovery sequence (3 messages)
- SMS conversation with no reply → SMS follow-up sequence (3 messages)
- Qualified lead not called back by owner → Nudge the OWNER (not the lead)

### Owner Nudge
If a qualified lead hasn't been called back within 30 minutes: "Reminder: Sarah Martinez is waiting for a callback about AC repair. Phone: (770) 555-1234. She called 35 minutes ago."

---

## 9. Review Request Automation

Triggered when owner marks a job as "completed" via dashboard (manual button click).

Flow: Wait 2 hours → Send review request SMS with Google review direct link → Wait 48 hours → Send one reminder → Done. Never more than one reminder.

Google review link: `https://search.google.com/local/writereview?placeid={google_place_id}` — configured during onboarding.

---

## 10. Business Owner Dashboard

### Pages

**Dashboard (Home):** Today stats (calls, missed, recovered, revenue), this month stats, recent activity feed, quick actions.

**Calls:** Paginated list, filterable by status and date. Click missed call → see resulting conversation.

**Leads:** Pipeline view by status (New → Qualifying → Qualified → Booked → Completed). Click lead → detail with conversation, timeline, actions.

**Conversations:** Split view — list on left, chat on right. AI vs human messages labeled. Take Over / Return to AI button. Voice transcripts and audio player for call recordings embedded.

**Appointments:** Calendar or list view. Actions: confirm, complete, cancel, no-show.

**Reports:** Weekly/monthly summaries. Charts: calls over time, revenue recovered. ROI calculation. Export as PDF/CSV.

**Settings:** Business info, hours, services (with pricing and bookable flag), AI greeting, AI instructions, notification prefs, Google Place ID, billing.

---

## 11. Admin System (Your Internal Tools)

### Admin Dashboard
Total active businesses, total calls/leads/revenue across all clients, client health scores (high activity = healthy, low activity = at risk).

### Business Management
List all clients with metrics. Onboard new client. Edit configuration. View any client's dashboard (for support). Pause/cancel service.

### System Monitoring
Webhook health, voice AI health, SMS delivery rates, error log, cost tracking per client.

### Onboarding Checklist (per client)
Business info collected → Twilio number provisioned → Voice AI assistant configured → Voice AI test call passed → Call forwarding set up and tested → Owner account created → Dashboard walkthrough sent → Notification prefs confirmed → Google Place ID configured → Stripe subscription created → System live → 24-hour check-in → 1-week check-in.

---

## 12. Billing & Subscription

### MVP (First 5 Clients)
Create Stripe subscription manually per client ($497/month). Store stripe_customer_id and stripe_subscription_id on business record. Stripe handles billing, invoicing, retries.

### Stripe Webhooks
- invoice.payment_succeeded → subscription_status = "active"
- invoice.payment_failed → Admin alert
- customer.subscription.deleted → subscription_status = "cancelled", pause service
- customer.subscription.paused → subscription_status = "paused", pause service

When paused/cancelled: Voice AI stops answering, SMS stops sending, dashboard read-only for 30 days, data retained 90 days.

---

## 13. Compliance & Legal

### TCPA
- Voice AI answering: Caller initiated contact — no TCPA issue
- SMS post-call confirmation: Direct response to caller's inquiry — permissible
- SMS follow-up sequences: Gray area, limit to 3 messages, include opt-out
- Review requests: Customer relationship exists, limit to 1 + 1 reminder
- STOP keywords honored immediately on all SMS

### A2P 10DLC
Required for business SMS. Brand registration ($4 one-time) + Campaign ($15/month) via Twilio. 1-5 day approval. Without it: 30-80% of SMS get carrier-filtered.

### Call Recording Consent
38 states + DC: one-party consent (sufficient). 11 states require two-party consent (CA, CT, FL, IL, MD, MA, MI, MT, NH, PA, WA). For two-party states, voice AI says briefly at start: "Just so you know, this call may be recorded for quality purposes." Keep it natural.

---

## 14. Technical Architecture

```
Caller → Twilio Voice → Your Server (missed call detection)
                              |
                    +---------+----------+
                    |         |          |
              Vapi.ai    Twilio SMS    Supabase (DB)
            (Voice AI)   (Secondary)   + Auth + Realtime
                    |         |          |
                    +---------+----------+
                              |
                         Next.js Dashboard
                         (Owner portal)
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12+) |
| Voice AI | Vapi.ai (MVP) → Custom Twilio+Deepgram+OpenAI+ElevenLabs (scale) |
| Telephony + SMS | Twilio |
| AI (SMS conversations) | OpenAI GPT-4o-mini |
| Database | PostgreSQL via Supabase |
| Auth | Supabase Auth |
| Real-time | Supabase Realtime |
| Task Queue | Celery + Redis |
| Frontend | Next.js 14 + Tailwind + shadcn/ui |
| Email | Resend |
| Billing | Stripe |
| Monitoring | Sentry |
| Hosting | Railway (backend) + Vercel (frontend) |

---

## 15. Database Schema Changes

### Additions to existing tables

```sql
-- calls table: add voice AI tracking
ALTER TABLE calls ADD COLUMN voice_ai_used BOOLEAN DEFAULT false;
ALTER TABLE calls ADD COLUMN voice_ai_transcript TEXT;
ALTER TABLE calls ADD COLUMN voice_ai_duration_seconds INTEGER;
ALTER TABLE calls ADD COLUMN voice_ai_cost DECIMAL(10,4);
ALTER TABLE calls ADD COLUMN recording_url TEXT;
ALTER TABLE calls ADD COLUMN line_type TEXT DEFAULT 'unknown';
  -- 'mobile', 'landline', 'voip', 'unknown'
ALTER TABLE calls ADD COLUMN vapi_call_id TEXT;

-- leads table: add qualification tracking
ALTER TABLE leads ADD COLUMN preferred_time TEXT;
ALTER TABLE leads ADD COLUMN qualification_source TEXT DEFAULT 'voice';
  -- 'voice', 'sms', 'mixed'

-- conversations table: add channel tracking
ALTER TABLE conversations ADD COLUMN channel TEXT DEFAULT 'sms';
  -- 'voice', 'sms', 'mixed'
ALTER TABLE conversations ADD COLUMN voice_transcript TEXT;

-- businesses table: add voice AI and review config
ALTER TABLE businesses ADD COLUMN vapi_assistant_id TEXT;
ALTER TABLE businesses ADD COLUMN google_place_id TEXT;
ALTER TABLE businesses ADD COLUMN call_recording_enabled BOOLEAN DEFAULT true;
ALTER TABLE businesses ADD COLUMN two_party_consent_state BOOLEAN DEFAULT false;
```

### New table: owner_nudges

```sql
CREATE TABLE owner_nudges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id     UUID NOT NULL REFERENCES businesses(id),
    lead_id         UUID NOT NULL REFERENCES leads(id),
    status          TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'sent', 'acknowledged')),
    sent_at         TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### New table: voice_ai_configs

```sql
CREATE TABLE voice_ai_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id     UUID NOT NULL REFERENCES businesses(id) UNIQUE,
    provider        TEXT NOT NULL DEFAULT 'vapi',
    provider_assistant_id TEXT,
    system_prompt_override TEXT,
    voice_id        TEXT,          -- ElevenLabs voice ID or similar
    greeting_override TEXT,        -- Custom first sentence
    max_call_duration_seconds INTEGER DEFAULT 300,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 16. API Endpoints

### Existing endpoints that need modification

```
POST /webhook/voice/call-completed
  CHANGE: Instead of triggering SMS text-back, transfer call to Voice AI.
  Fall back to SMS if voice AI is unavailable.

POST /webhook/sms/incoming
  KEEP: Still handles inbound SMS. No changes needed.

GET /api/dashboard/stats
  ADD: Include voice AI stats (calls handled by AI, avg call duration)

GET /api/conversations/:id
  ADD: Return voice transcript and recording URL alongside messages
```

### New endpoints

```
POST /webhook/vapi/call-ended
  Receives end-of-call data from Vapi: transcript, extracted data,
  duration, recording URL. Creates/updates lead, conversation, and
  call records. Triggers owner notification.

POST /webhook/vapi/function-call
  Receives real-time function calls from Vapi during active calls.
  save_lead_info: updates lead record with extracted data.
  flag_emergency: triggers immediate owner notification.
  request_human_callback: flags conversation for human follow-up.

POST /webhook/stripe
  Handles Stripe subscription events: payment succeeded, failed,
  cancelled, paused.

POST /api/admin/businesses/:id/configure-voice
  Creates/updates Vapi assistant for a business with their specific
  configuration (services, hours, prompt customizations).

POST /api/admin/businesses/:id/test-call
  Initiates a test call to the Twilio number to verify voice AI
  is working correctly. Returns call status and transcript.

POST /api/leads/:id/mark-completed
  Marks a lead/job as completed. Triggers review request automation
  (delayed by 2 hours via Celery task).

POST /api/leads/:id/request-review
  Manually trigger a review request for a specific lead.

GET /api/calls/:id/recording
  Returns the voice AI call recording URL (presigned, time-limited).

GET /api/calls/:id/transcript
  Returns the voice AI call transcript.

GET /api/admin/monitoring/health
  System health: Twilio webhook status, Vapi connectivity,
  SMS delivery rates, database connection, Redis connection.

GET /api/admin/monitoring/costs
  Per-client cost breakdown: Twilio voice minutes, Twilio SMS count,
  Vapi minutes, OpenAI tokens.
```

### Celery Tasks (New/Modified)

```
send_post_call_sms (NEW)
  Triggered after voice AI call ends for mobile callers.
  Sends confirmation SMS.

send_incomplete_call_followup (NEW)
  Triggered when voice call ends but lead is not fully qualified.
  Starts SMS recovery sequence.

send_owner_nudge (NEW)
  Triggered 30 minutes after a lead is qualified if the owner
  hasn't acknowledged or called back. Sends reminder SMS to owner.

send_review_request (MODIFY)
  Now triggered by lead marked as "completed" instead of appointment.
  Includes Google review direct link.

compute_daily_metrics (MODIFY)
  Include voice AI metrics: calls handled by AI, avg duration,
  qualification rate, cost.
```

---

## 17. Voice AI Technical Implementation

### Vapi Integration Flow

**Setup (per business):**
1. Create a Vapi assistant via Vapi API with the business-specific system prompt
2. Configure the assistant with function calling tools (save_lead_info, flag_emergency, request_human_callback)
3. Set the assistant's webhook URL to your server for function call execution
4. Store the vapi_assistant_id on the business record

**Call transfer (per missed call):**
When a missed call is detected, instead of sending SMS, use Twilio's `<Dial>` or `<Connect>` to transfer the live call to Vapi.

```python
# In the call-completed webhook, when a call is missed:

# Option A: Transfer via Twilio SIP to Vapi phone number
response = VoiceResponse()
dial = response.dial()
dial.sip(f"sip:{vapi_phone_number}@sip.vapi.ai")

# Option B: Use Vapi's Twilio integration (Vapi provides a webhook URL)
# Configure the Twilio number's "no-answer" URL to point to Vapi directly

# Option C: Use Vapi's outbound call to bridge
# Your server tells Vapi to call the caller back immediately
# Less ideal due to the brief disconnect
```

The exact integration method depends on Vapi's current Twilio integration approach. Check Vapi's documentation for the most up-to-date method. The key requirement: the caller should NOT experience a disconnect. The call should transfer seamlessly from ringing to the AI answering.

**Receiving call results:**
Vapi sends a webhook when the call ends:

```json
{
  "call_id": "vapi_call_123",
  "status": "completed",
  "duration_seconds": 147,
  "transcript": [
    {"role": "assistant", "content": "Hi! Thanks for calling Smith's..."},
    {"role": "user", "content": "Yeah my AC isn't working..."}
  ],
  "recording_url": "https://...",
  "extracted_data": {
    "name": "Sarah Martinez",
    "service_needed": "AC not blowing cold",
    "urgency": "soon",
    "address": "123 Oak Street, Marietta",
    "preferred_time": "tomorrow morning"
  },
  "cost": 0.12
}
```

Your /webhook/vapi/call-ended handler processes this, creates/updates all records, and triggers notifications.

### Fallback: Voice AI Unavailable

If Vapi is unreachable or returns an error during call transfer:

```python
# Fallback to SMS text-back (existing logic)
try:
    transfer_to_vapi(call, business)
except VapiUnavailableError:
    # Log the failure
    logger.error(f"Vapi unavailable for call {call.id}")

    # Fall back to voicemail + SMS
    response = VoiceResponse()
    response.say(
        f"Sorry we missed your call at {business.name}. "
        f"We'll text you right away to help."
    )

    # Trigger SMS text-back flow
    await send_initial_sms(caller_phone, business, conversation)
```

This ensures no lead is ever lost, even if the voice AI platform goes down.

### Fallback: Landline Callers (No SMS Available)

If line type is "landline" and voice AI call is incomplete:

```python
# Can't send SMS follow-up — notify owner for manual callback
await notify_owner(
    business=business,
    event="incomplete_call_landline",
    data={
        "caller_phone": caller_phone,
        "transcript": partial_transcript,
        "what_we_know": extracted_data,
    }
)
# Message: "Landline caller (770) 555-1234 — call incomplete.
#           They need: AC repair. Please call them back."
```

---

## 18. Deployment & Infrastructure

### Production Setup

| Service | Provider | Estimated Cost |
|---------|---------|---------------|
| Backend API | Railway Pro | $20/month |
| Celery Worker | Railway Pro | $10/month |
| Celery Beat (scheduler) | Railway Pro | $5/month |
| Redis | Railway Redis addon | $5/month |
| Frontend | Vercel Free/Pro | $0-20/month |
| Database | Supabase Pro | $25/month |
| Domain + SSL | Cloudflare | $10/year |
| Error Tracking | Sentry Free | $0 |
| Uptime Monitoring | UptimeRobot Free | $0 |
| **Total fixed** | | **$65-85/month** |

### Per-Client Variable Costs

| Item | Low (50 missed calls/mo) | Medium (100) | High (200) |
|------|-------------------------|-------------|-----------|
| Twilio number | $1.15 | $1.15 | $1.15 |
| Twilio voice (forwarding) | $3.50 | $7.00 | $14.00 |
| Vapi voice AI (~2.5 min avg) | $6.25 | $12.50 | $25.00 |
| Twilio SMS (confirmations + follow-ups) | $0.50 | $1.00 | $2.00 |
| OpenAI (SMS conversations) | $0.02 | $0.05 | $0.10 |
| Twilio Lookup (line type) | $0.25 | $0.50 | $1.00 |
| **Total per client** | **$11.67** | **$22.20** | **$43.25** |

At $497/month per client: **95-97% gross margin.**

### Environment Variables

```bash
# Twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=

# OpenAI
OPENAI_API_KEY=

# Vapi
VAPI_API_KEY=
VAPI_WEBHOOK_SECRET=

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
DATABASE_URL=

# Redis
REDIS_URL=

# App
BASE_URL=              # Your server's public URL
ENVIRONMENT=           # development | production
ALLOWED_ORIGINS=       # CORS origins for frontend
ADMIN_API_KEY=         # Secret key for admin endpoints

# Email
RESEND_API_KEY=
EMAIL_FROM_ADDRESS=

# Stripe
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# Frontend
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=

# Business config
FOLLOW_UP_DELAY_MINUTES=120,1440  # 2 hours, 24 hours between follow-ups
OWNER_NUDGE_DELAY_MINUTES=30
```

---

## 19. Cost Model

### Revenue vs Cost at Scale

| Clients | Monthly Revenue | Total COGS | Gross Profit | Margin |
|---------|---------------|-----------|-------------|--------|
| 1 | $497 | $87-107 | $390-410 | 78-83% |
| 5 | $2,485 | $176-196 | $2,289-2,309 | 92-93% |
| 10 | $4,970 | $287-307 | $4,663-4,683 | 94-95% |
| 20 | $9,940 | $509-549 | $9,391-9,431 | 94-95% |

COGS breakdown: Fixed platform costs ($65-85) + per-client variable costs ($22 avg x N clients).

Voice AI (Vapi) is the largest variable cost at ~$12.50/client/month for medium usage. At scale, migrating to custom pipeline reduces this to ~$5-8/client/month.

---

## 20. Build Sequence

### What Already Exists (Current Codebase)

The current repo (github.com/joelbyler272/hvac-ai-recovery) has:
- FastAPI backend with full project structure
- Twilio voice webhooks (incoming call + missed call detection)
- Twilio SMS webhooks (inbound messages, opt-out/opt-in handling)
- AI SMS conversation engine (OpenAI GPT-4o-mini with system prompt, function calling extraction)
- Service-aware pricing in AI prompts
- Follow-up sequence via Celery (3 messages with configurable delays)
- Notification system (SMS + email to owner with quiet hours)
- Review request automation (with 48hr reminder)
- Daily metrics computation + weekly report email
- Next.js dashboard with: stats, call log, lead pipeline, conversation view with takeover, appointments, reports, settings
- Supabase Auth integration with dev mode
- Supabase Realtime for live dashboard updates
- Admin API for business management
- Docker Compose for local dev
- Alembic migrations (2 versions)
- Supabase SQL scripts (RLS, realtime, auth triggers)

### What Needs to Be Built

**Priority 1: Voice AI Integration (Week 1)**
- [ ] Sign up for Vapi.ai, get API credentials
- [ ] Build Vapi assistant creation endpoint (/api/admin/businesses/:id/configure-voice)
- [ ] Modify /webhook/voice/call-completed to transfer missed calls to Vapi instead of SMS
- [ ] Build /webhook/vapi/call-ended to process voice AI results
- [ ] Build /webhook/vapi/function-call to handle real-time data extraction
- [ ] Add Twilio Lookup API call for line type detection before routing
- [ ] Add fallback to SMS text-back if Vapi is unavailable
- [ ] Add call recording storage and playback
- [ ] Add voice transcript to conversation view in dashboard
- [ ] Database migration: add voice AI columns to calls, leads, conversations, businesses
- [ ] Test: call Twilio number → let it miss → hear voice AI → have full conversation → verify lead created

**Priority 2: Production Deployment (Week 1, parallel)**
- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Vercel
- [ ] Configure Supabase production project
- [ ] Set up all environment variables
- [ ] Verify Twilio webhooks reach production server
- [ ] Set up Sentry error tracking
- [ ] Start A2P 10DLC registration in Twilio Console

**Priority 3: Post-Call SMS & Incomplete Recovery (Week 2)**
- [ ] Build send_post_call_sms Celery task
- [ ] Build send_incomplete_call_followup Celery task
- [ ] Add landline-specific handling (notify owner for manual callback)
- [ ] Verify SMS delivery with 10DLC registration

**Priority 4: Owner Nudge System (Week 2)**
- [ ] Build owner_nudges table and logic
- [ ] Build send_owner_nudge Celery task (30 min after qualification)
- [ ] Build nudge acknowledgment endpoint

**Priority 5: Review Requests with Google Link (Week 2)**
- [ ] Add google_place_id to business settings
- [ ] Modify review request SMS to include direct Google review link
- [ ] Add "Mark Completed" button on lead detail page in dashboard
- [ ] Wire completion → review request trigger

**Priority 6: Stripe Billing (Week 2-3)**
- [ ] Build /webhook/stripe endpoint for subscription events
- [ ] Build subscription status management (active/paused/cancelled → affects service)
- [ ] Add billing info to Settings page in dashboard
- [ ] Create Stripe product and price for $497/month plan

**Priority 7: Error Handling & Resilience (Week 3)**
- [ ] Add fallback SMS if OpenAI is down during SMS conversations
- [ ] Add conversation staleness check (>7 days → start fresh)
- [ ] Add rate limiting on webhook endpoints
- [ ] Add request validation for Twilio webhook signatures
- [ ] Add Vapi webhook signature validation

**Priority 8: Admin Monitoring (Week 3)**
- [ ] Build /api/admin/monitoring/health endpoint
- [ ] Build /api/admin/monitoring/costs endpoint
- [ ] Build onboarding checklist view in admin dashboard
- [ ] Add per-client health metrics (activity level, churn risk)

**Priority 9: Polish & First Client (Week 3-4)**
- [ ] Landing page (Carrd or simple Next.js page)
- [ ] Call recording consent message for two-party consent states
- [ ] Test complete flow with a friend pretending to be an HVAC caller
- [ ] Prepare onboarding Loom video for owners
- [ ] Onboard first beta client
- [ ] Monitor first 48 hours intensively

---

## 21. Success Metrics

### For Each Client

| Metric | Target |
|--------|--------|
| Missed calls detected | 100% of forwarded missed calls |
| Voice AI answer rate | >95% of missed calls (remainder = fallback to SMS) |
| Lead qualification rate | >60% of AI-answered calls result in a qualified lead |
| Owner notification latency | <60 seconds from call end to SMS notification |
| SMS delivery rate | >95% (requires 10DLC) |
| Client churn | <5% monthly |

### For the Business

| Milestone | Target |
|-----------|--------|
| First beta client | Week 4 |
| First paying client | Week 6 |
| 5 paying clients ($2,485 MRR) | Month 3 |
| 10 paying clients ($4,970 MRR) | Month 5 |
| First case study published | Month 3 |
| Open-source repo launched | Month 4-5 |

---

## Appendix: Key Design Decisions

**Why voice AI first instead of SMS text-back?**
SMS text-back is what every GoHighLevel reseller offers. It loses landline callers, non-texters, and anyone who doesn't check texts quickly. Voice AI answers the actual call — the caller never hangs up, never calls a competitor. It's a fundamentally stronger product with an actual technical moat.

**Why Vapi before custom?**
Speed to market. Vapi gets voice AI working in days. Custom pipeline takes weeks. Revenue > engineering purity. Migrate when volume justifies it.

**Why $497/month?**
HVAC companies lose $3,000-$15,000/month in missed calls. $497 is clearly below the value delivered. It's low enough to be a no-brainer, high enough to be taken seriously. $250-350 attracts tire-kickers. $497 attracts businesses that actually miss calls and know it.

**Why AGPL-3.0 for open source?**
Requires anyone who deploys modifications to share their changes. Creates a natural path to commercial licensing. Same license as MongoDB, Grafana, and n8n — proven model.

**Why not integrate with ServiceTitan/Housecall Pro/Jobber?**
Not for MVP. CRM integrations are complex, require certification, and each client uses a different CRM. The notification + dashboard approach works for the first 10-20 clients. Add CRM integrations when demand justifies the engineering investment.
