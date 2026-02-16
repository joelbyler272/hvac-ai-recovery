# HVAC AI Missed Call Recovery System — Technical Architecture Specification

**Version:** 1.0
**Purpose:** Complete technical spec for building the MVP. Hand this document directly to Claude Code.
**Target build time:** 2–3 weeks for a solo developer

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Tech Stack](#3-tech-stack)
4. [Core Call Flow](#4-core-call-flow)
5. [Database Schema](#5-database-schema)
6. [API Endpoints](#6-api-endpoints)
7. [Twilio Integration](#7-twilio-integration)
8. [AI Conversation Engine](#8-ai-conversation-engine)
9. [Appointment Booking](#9-appointment-booking)
10. [Notification System](#10-notification-system)
11. [Review Request Automation](#11-review-request-automation)
12. [Dashboard & Frontend](#12-dashboard--frontend)
13. [Authentication & Multi-Tenancy](#13-authentication--multi-tenancy)
14. [Compliance & Legal](#14-compliance--legal)
15. [Infrastructure & Deployment](#15-infrastructure--deployment)
16. [Phase 2: Voice AI](#16-phase-2-voice-ai)
17. [Phase 3: Database Reactivation](#17-phase-3-database-reactivation)
18. [Cost Model](#18-cost-model)
19. [Open-Source Considerations](#19-open-source-considerations)
20. [Build Sequence](#20-build-sequence)

---

## 1. System Overview

### What the system does

When an HVAC company's phone rings and nobody answers:

1. The system detects the missed call within seconds
2. Sends an instant SMS to the caller: "Hey, sorry we missed your call! This is [Company Name]. How can we help?"
3. An AI-powered SMS conversation qualifies the lead (what service they need, urgency, address, preferred time)
4. When the lead is qualified, the system books an appointment or notifies the business owner
5. The business owner gets a real-time notification: "New lead: AC not cooling at 123 Main St. Booked for tomorrow 2pm."
6. A dashboard shows all recovered calls, conversations, appointments, and estimated revenue

### What it does NOT do (in MVP)

- Answer live calls with voice AI (Phase 2)
- Integrate with ServiceTitan/Housecall Pro/Jobber (Phase 2+)
- Run outbound reactivation campaigns (Phase 3)
- Handle multiple languages (future)
- Process payments (out of scope)

### Multi-tenant by design

The system serves multiple HVAC companies simultaneously. Every data model is scoped to a `business_id`. A single deployment handles all clients — you do NOT spin up separate instances per client.

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CALLER (Homeowner)                          │
│                     Calls HVAC company phone                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │    TWILIO VOICE      │
                    │  (Call Forwarding)   │
                    │                     │
                    │  Ring HVAC phone    │
                    │  for 20 seconds     │
                    │  ↓                  │
                    │  No answer?         │
                    │  → StatusCallback   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │     YOUR SERVER      │
                    │    (FastAPI/Python)  │
                    │                     │
                    │  /webhook/call-status│──────┐
                    │  /webhook/sms-in    │      │
                    │  /api/*             │      │
                    └──────────┬──────────┘      │
                               │                 │
              ┌────────────────┼─────────────────┼────────────┐
              │                │                 │            │
    ┌─────────▼──────┐ ┌──────▼──────┐ ┌───────▼─────┐ ┌───▼────────┐
    │   TWILIO SMS   │ │  OPENAI API │ │  POSTGRESQL  │ │  NEXT.JS   │
    │  (Send/Recv)   │ │  (GPT-4o-   │ │  (Supabase)  │ │ DASHBOARD  │
    │                │ │   mini)     │ │              │ │            │
    │  Text caller   │ │  Qualify    │ │  Businesses  │ │  Owner     │
    │  back instantly│ │  the lead   │ │  Calls       │ │  portal    │
    │                │ │  via SMS    │ │  Convos      │ │            │
    └────────────────┘ └─────────────┘ │  Messages    │ └────────────┘
                                       │  Leads       │
                                       │  Appointments│
                                       └──────────────┘
```

---

## 3. Tech Stack

### Backend (Python)

| Component | Technology | Why |
|-----------|-----------|-----|
| Framework | **FastAPI** | Async by default, great for webhooks, auto-generates OpenAPI docs |
| Runtime | **Python 3.12+** | Best ecosystem for AI/ML, Twilio SDK is excellent |
| Database | **PostgreSQL** via Supabase | Managed, real-time subscriptions, built-in auth, generous free tier |
| ORM | **SQLAlchemy 2.0** + Alembic | Type-safe, migration support, async compatible |
| Task Queue | **Celery** + Redis (or **ARQ** for lightweight) | Delayed SMS follow-ups, scheduled campaigns, async processing |
| Caching | **Redis** | Conversation state, rate limiting, session cache |

### Frontend (TypeScript)

| Component | Technology | Why |
|-----------|-----------|-----|
| Framework | **Next.js 14+** (App Router) | SSR, API routes, excellent DX |
| Styling | **Tailwind CSS** + **shadcn/ui** | Fast to build, professional look, accessible components |
| Charts | **Recharts** or **Tremor** | Clean data visualization for the dashboard |
| Auth | **Supabase Auth** | JWT-based, handles magic links and OAuth |
| State | **TanStack Query** | Server state management, auto-refetch |
| Real-time | **Supabase Realtime** | Live updates on dashboard when new calls come in |

### External Services

| Service | Purpose | Estimated Cost |
|---------|---------|---------------|
| **Twilio** | Voice call handling + SMS | ~$1.15/number/mo + $0.0085/SMS + $0.014/min voice |
| **OpenAI** | GPT-4o-mini for SMS conversations | ~$0.15/1M input tokens, $0.60/1M output tokens |
| **Supabase** | Database + Auth + Realtime | Free tier → $25/mo Pro |
| **Redis Cloud** | Task queue + caching | Free tier → $5/mo |
| **Resend** | Transactional email (notifications, reports) | Free tier (100/day) → $20/mo |
| **Vercel** | Frontend hosting | Free tier → $20/mo |
| **Railway** or **Render** | Backend hosting | $5–$25/mo |

### Total infrastructure cost per client: ~$3–$15/month

---

## 4. Core Call Flow

### Flow 1: Missed Call → AI SMS Conversation → Lead Captured

This is the entire MVP in one flow.

```
1. Caller dials HVAC company's Twilio number
   │
2. Twilio receives call, executes TwiML:
   │  - <Dial> to HVAC company's real phone
   │  - timeout="20" (ring for 20 seconds)
   │  - action="/webhook/call-completed" (fires after dial ends)
   │
3. HVAC phone rings for 20 seconds
   │
4a. IF ANSWERED → Call connects normally. Log call as "answered." Done.
   │
4b. IF NOT ANSWERED → Twilio sends POST to /webhook/call-completed
   │  with DialCallStatus = "no-answer" | "busy" | "failed"
   │
5. Server receives webhook:
   │  - Extracts caller phone number (From)
   │  - Looks up business by Twilio number (To)
   │  - Checks: is this number already in an active conversation? (dedup)
   │  - Checks: is this number on the opt-out list? (compliance)
   │  - Creates Call record in DB (status: "missed")
   │  - Creates Lead record (status: "new")
   │  - Creates Conversation record (status: "active")
   │
6. Server triggers immediate SMS via Twilio:
   │  "Hey! Sorry we missed your call. This is [Business Name].
   │   How can we help you today?"
   │  - Creates Message record in DB
   │  - Logs SMS sent timestamp
   │
7. Caller replies via SMS
   │  → Twilio receives SMS, sends POST to /webhook/sms-incoming
   │
8. Server receives inbound SMS:
   │  - Matches to existing Conversation by phone number + business
   │  - Appends message to conversation history
   │  - Sends conversation history + system prompt to OpenAI
   │  - AI generates qualifying response
   │  - Sends AI response via Twilio SMS
   │  - Updates Lead status based on qualification progress
   │
9. Conversation continues (steps 7-8 repeat) until:
   │  a. Lead is fully qualified → notify business owner, attempt booking
   │  b. Caller stops responding → enter follow-up sequence
   │  c. Caller opts out ("STOP") → mark opted out, cease messaging
   │  d. Conversation times out (48h no response) → mark as stale
   │
10. When lead is qualified:
    - Update Lead status to "qualified"
    - Send notification to business owner (SMS + email + dashboard)
    - If booking is enabled, offer time slots to caller
    - Create Appointment record if booked
```

### Flow 2: Follow-Up Sequence (No Response)

```
If caller doesn't reply to initial SMS within 2 hours:
  → Send follow-up #1: "Just checking in — did you still need help
     with [service if known / "anything"]? Happy to get you scheduled."

If no reply after 24 hours:
  → Send follow-up #2: "Hey [if name known], wanted to make sure you're
     taken care of. We have availability this week if you need
     [service]. Reply anytime!"

If no reply after 72 hours:
  → Send final follow-up: "Last note from us — if you need [service]
     down the road, just text this number anytime. We're here to help.
     - [Business Name]"
  → Mark conversation as "closed_no_response"
  → Mark lead as "unresponsive"
```

### Flow 3: Human Takeover

```
At any point, the business owner can:
  1. View the conversation on the dashboard
  2. Click "Take Over" button
  3. System marks conversation as "human_active"
  4. All subsequent messages from the caller route to the owner
     (via dashboard or forwarded SMS)
  5. AI stops responding automatically
  6. Owner can click "Return to AI" to re-enable automation
```

---

## 5. Database Schema

### Core Tables

```sql
-- ============================================
-- BUSINESSES (your HVAC company clients)
-- ============================================
CREATE TABLE businesses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,                    -- "Smith's Heating & Air"
    owner_name      TEXT NOT NULL,                    -- "John Smith"
    owner_email     TEXT NOT NULL,
    owner_phone     TEXT NOT NULL,                    -- for notifications
    business_phone  TEXT NOT NULL,                    -- their real phone number
    twilio_number   TEXT UNIQUE NOT NULL,             -- assigned Twilio number
    timezone        TEXT NOT NULL DEFAULT 'America/New_York',
    business_hours  JSONB NOT NULL DEFAULT '{
        "monday":    {"open": "08:00", "close": "17:00"},
        "tuesday":   {"open": "08:00", "close": "17:00"},
        "wednesday": {"open": "08:00", "close": "17:00"},
        "thursday":  {"open": "08:00", "close": "17:00"},
        "friday":    {"open": "08:00", "close": "17:00"},
        "saturday":  null,
        "sunday":    null
    }',
    services        TEXT[] NOT NULL DEFAULT '{}',     -- {"AC Repair", "Heating", "Maintenance"}
    avg_job_value   DECIMAL(10,2) DEFAULT 350.00,    -- for revenue estimation
    ai_greeting     TEXT,                             -- custom first message override
    ai_instructions TEXT,                             -- custom AI behavior notes
    notification_prefs JSONB NOT NULL DEFAULT '{
        "sms": true,
        "email": true,
        "quiet_start": "21:00",
        "quiet_end": "07:00"
    }',
    subscription_status TEXT NOT NULL DEFAULT 'active'
        CHECK (subscription_status IN ('trial', 'active', 'paused', 'cancelled')),
    stripe_customer_id  TEXT,
    stripe_subscription_id TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- CALLS (every inbound call)
-- ============================================
CREATE TABLE calls (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id     UUID NOT NULL REFERENCES businesses(id),
    twilio_call_sid TEXT UNIQUE NOT NULL,
    caller_phone    TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'ringing'
        CHECK (status IN ('ringing', 'answered', 'missed', 'voicemail', 'busy', 'failed')),
    duration_seconds INTEGER,
    is_after_hours  BOOLEAN NOT NULL DEFAULT false,
    recording_url   TEXT,                             -- voicemail recording if any
    transcription   TEXT,                             -- voicemail transcription
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_calls_business ON calls(business_id, created_at DESC);
CREATE INDEX idx_calls_caller ON calls(caller_phone, business_id);

-- ============================================
-- LEADS (a person who called)
-- ============================================
CREATE TABLE leads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id     UUID NOT NULL REFERENCES businesses(id),
    phone           TEXT NOT NULL,
    name            TEXT,                              -- extracted during AI conversation
    email           TEXT,
    address         TEXT,
    service_needed  TEXT,                              -- "AC not cooling"
    urgency         TEXT CHECK (urgency IN ('emergency', 'soon', 'flexible', 'unknown')),
    status          TEXT NOT NULL DEFAULT 'new'
        CHECK (status IN (
            'new',              -- just called, no conversation yet
            'contacted',        -- first SMS sent
            'qualifying',       -- AI conversation in progress
            'qualified',        -- all info collected
            'booked',           -- appointment scheduled
            'completed',        -- job done
            'unresponsive',     -- no reply after follow-ups
            'opted_out',        -- sent STOP
            'lost'              -- went with competitor
        )),
    source          TEXT NOT NULL DEFAULT 'missed_call'
        CHECK (source IN ('missed_call', 'web_form', 'reactivation', 'manual')),
    estimated_value DECIMAL(10,2),                    -- avg_job_value from business
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(business_id, phone)                        -- one lead per phone per business
);

CREATE INDEX idx_leads_business_status ON leads(business_id, status);

-- ============================================
-- CONVERSATIONS (SMS thread with a lead)
-- ============================================
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id     UUID NOT NULL REFERENCES businesses(id),
    lead_id         UUID NOT NULL REFERENCES leads(id),
    call_id         UUID REFERENCES calls(id),        -- the missed call that started this
    status          TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN (
            'active',            -- AI is handling
            'human_active',      -- owner took over
            'follow_up',         -- in follow-up sequence
            'closed_booked',     -- appointment made
            'closed_no_response',-- gave up after follow-ups
            'closed_opted_out',  -- STOP received
            'closed_manual'      -- owner closed it
        )),
    follow_up_count INTEGER NOT NULL DEFAULT 0,
    next_follow_up_at TIMESTAMPTZ,                    -- when to send next follow-up
    qualification_data JSONB DEFAULT '{}',            -- structured data from AI
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_convos_business ON conversations(business_id, status);
CREATE INDEX idx_convos_followup ON conversations(next_follow_up_at)
    WHERE status = 'follow_up';

-- ============================================
-- MESSAGES (individual SMS messages)
-- ============================================
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    business_id     UUID NOT NULL REFERENCES businesses(id),
    direction       TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    sender_type     TEXT NOT NULL CHECK (sender_type IN ('caller', 'ai', 'human')),
    body            TEXT NOT NULL,
    twilio_message_sid TEXT,
    status          TEXT NOT NULL DEFAULT 'sent'
        CHECK (status IN ('queued', 'sent', 'delivered', 'failed', 'received')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_convo ON messages(conversation_id, created_at);

-- ============================================
-- APPOINTMENTS
-- ============================================
CREATE TABLE appointments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id     UUID NOT NULL REFERENCES businesses(id),
    lead_id         UUID NOT NULL REFERENCES leads(id),
    conversation_id UUID REFERENCES conversations(id),
    scheduled_date  DATE NOT NULL,
    scheduled_time  TIME NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 60,
    service_type    TEXT,
    address         TEXT,
    status          TEXT NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show')),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_appointments_business ON appointments(business_id, scheduled_date);

-- ============================================
-- REVIEW REQUESTS
-- ============================================
CREATE TABLE review_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id     UUID NOT NULL REFERENCES businesses(id),
    lead_id         UUID NOT NULL REFERENCES leads(id),
    phone           TEXT NOT NULL,
    review_url      TEXT NOT NULL,                     -- direct Google review link
    status          TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'sent', 'reminded', 'completed', 'opted_out')),
    sent_at         TIMESTAMPTZ,
    reminder_sent_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- OPT-OUTS (TCPA compliance)
-- ============================================
CREATE TABLE opt_outs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone           TEXT NOT NULL,
    business_id     UUID REFERENCES businesses(id),   -- NULL = global opt-out
    reason          TEXT DEFAULT 'stop_keyword',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(phone, business_id)
);

CREATE INDEX idx_opt_outs_phone ON opt_outs(phone);

-- ============================================
-- AUDIT LOG (everything that happens)
-- ============================================
CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id     UUID REFERENCES businesses(id),
    entity_type     TEXT NOT NULL,                     -- 'call', 'lead', 'conversation', etc.
    entity_id       UUID NOT NULL,
    action          TEXT NOT NULL,                     -- 'created', 'updated', 'sms_sent', etc.
    details         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_business ON audit_log(business_id, created_at DESC);

-- ============================================
-- DASHBOARD METRICS (pre-computed daily)
-- ============================================
CREATE TABLE daily_metrics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id     UUID NOT NULL REFERENCES businesses(id),
    date            DATE NOT NULL,
    total_calls     INTEGER NOT NULL DEFAULT 0,
    missed_calls    INTEGER NOT NULL DEFAULT 0,
    recovered_calls INTEGER NOT NULL DEFAULT 0,       -- missed calls that became conversations
    leads_captured  INTEGER NOT NULL DEFAULT 0,
    leads_qualified INTEGER NOT NULL DEFAULT 0,
    appointments_booked INTEGER NOT NULL DEFAULT 0,
    estimated_revenue DECIMAL(10,2) NOT NULL DEFAULT 0,
    messages_sent   INTEGER NOT NULL DEFAULT 0,
    messages_received INTEGER NOT NULL DEFAULT 0,
    UNIQUE(business_id, date)
);
```

---

## 6. API Endpoints

### Webhook Endpoints (Twilio → Your Server)

```
POST /webhook/voice/incoming
  - Twilio sends this when a call comes in to your number
  - Returns TwiML to ring the HVAC company's phone

POST /webhook/voice/call-completed
  - Twilio sends this after the <Dial> completes
  - DialCallStatus tells you if it was answered or missed
  - If missed: trigger the SMS flow

POST /webhook/sms/incoming
  - Twilio sends this when an SMS arrives
  - Match to conversation, run AI, send response

POST /webhook/sms/status
  - Twilio delivery status updates
  - Track delivered/failed for each message
```

### Dashboard API (Frontend → Backend)

```
# Authentication
POST   /api/auth/login           - Email magic link
POST   /api/auth/verify          - Verify magic link token
GET    /api/auth/me              - Current user + business

# Dashboard
GET    /api/dashboard/stats      - Summary metrics (calls, leads, revenue)
GET    /api/dashboard/recent     - Recent activity feed

# Calls
GET    /api/calls                - List calls (paginated, filterable)
GET    /api/calls/:id            - Call detail

# Leads
GET    /api/leads                - List leads (filterable by status)
GET    /api/leads/:id            - Lead detail with full conversation
PATCH  /api/leads/:id            - Update lead (status, notes)

# Conversations
GET    /api/conversations        - List conversations
GET    /api/conversations/:id    - Full conversation with messages
POST   /api/conversations/:id/takeover    - Human takes over from AI
POST   /api/conversations/:id/return-ai   - Return to AI handling
POST   /api/conversations/:id/message     - Send manual message

# Appointments
GET    /api/appointments         - List appointments
POST   /api/appointments         - Create appointment manually
PATCH  /api/appointments/:id     - Update appointment status

# Settings
GET    /api/settings             - Business settings
PATCH  /api/settings             - Update settings (hours, AI greeting, etc.)

# Reports
GET    /api/reports/weekly       - Weekly summary
GET    /api/reports/monthly      - Monthly summary with ROI calc
```

### Admin API (Your Internal Use)

```
# Business Management
GET    /api/admin/businesses           - List all client businesses
POST   /api/admin/businesses           - Onboard new client
PATCH  /api/admin/businesses/:id       - Update client config
POST   /api/admin/businesses/:id/provision  - Provision Twilio number

# System Health
GET    /api/admin/health               - System health check
GET    /api/admin/metrics              - Cross-client metrics
```

---

## 7. Twilio Integration

### Phone Number Setup

Each HVAC client gets their own Twilio local number. When onboarding a new client:

```python
# Provision a local number in the client's area code
from twilio.rest import Client

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Search for available numbers in client's area
numbers = client.available_phone_numbers("US").local.list(
    area_code=client_area_code,
    voice_enabled=True,
    sms_enabled=True,
    limit=5
)

# Purchase the number
purchased = client.incoming_phone_numbers.create(
    phone_number=numbers[0].phone_number,
    voice_url=f"{BASE_URL}/webhook/voice/incoming",
    voice_method="POST",
    sms_url=f"{BASE_URL}/webhook/sms/incoming",
    sms_method="POST",
    status_callback=f"{BASE_URL}/webhook/sms/status",
    status_callback_method="POST"
)
```

**Call forwarding setup:** The HVAC company forwards their existing business number to the Twilio number. This way callers still dial the same number they've always used.

Alternatively, the HVAC company can set up conditional forwarding: forward to Twilio only when busy or no answer. This depends on their phone carrier.

### Voice Webhook: Incoming Call TwiML

```python
@app.post("/webhook/voice/incoming")
async def voice_incoming(request: Request):
    """
    When a call comes in:
    1. Ring the HVAC company's actual phone for 20 seconds
    2. If they answer, connect the call normally
    3. If they don't answer, the action URL fires
    """
    form = await request.form()
    from_number = form.get("From")
    to_number = form.get("To")

    # Look up which business this Twilio number belongs to
    business = await get_business_by_twilio_number(to_number)

    if not business:
        # Unknown number — just ring through
        response = VoiceResponse()
        response.say("Sorry, this number is not configured.")
        return Response(content=str(response), media_type="application/xml")

    # Log the incoming call
    call = await create_call_record(
        business_id=business.id,
        twilio_call_sid=form.get("CallSid"),
        caller_phone=from_number,
        status="ringing",
        is_after_hours=is_after_hours(business)
    )

    response = VoiceResponse()

    # Ring their business phone for 20 seconds
    dial = response.dial(
        timeout=20,
        action=f"{BASE_URL}/webhook/voice/call-completed?call_id={call.id}",
        method="POST",
        caller_id=to_number  # Show the Twilio number as caller ID
    )
    dial.number(
        business.business_phone,
        status_callback=f"{BASE_URL}/webhook/voice/dial-status",
        status_callback_event="initiated ringing answered completed"
    )

    return Response(content=str(response), media_type="application/xml")
```

### Voice Webhook: Call Completed (Missed Call Detection)

```python
@app.post("/webhook/voice/call-completed")
async def call_completed(request: Request, call_id: str):
    """
    Fires after the <Dial> completes.
    DialCallStatus tells us what happened:
    - "completed" = call was answered
    - "no-answer" = nobody picked up
    - "busy" = line was busy
    - "failed" = technical failure
    - "canceled" = caller hung up before answer
    """
    form = await request.form()
    dial_status = form.get("DialCallStatus")
    caller_phone = form.get("From")
    twilio_number = form.get("To")

    call = await get_call(call_id)
    business = await get_business(call.business_id)

    if dial_status == "completed":
        # Call was answered normally — just log it
        await update_call(call.id, status="answered",
                         duration=int(form.get("DialCallDuration", 0)))

        response = VoiceResponse()
        return Response(content=str(response), media_type="application/xml")

    # === MISSED CALL — This is where the magic happens ===

    await update_call(call.id, status="missed")

    # Check opt-out list
    if await is_opted_out(caller_phone, business.id):
        response = VoiceResponse()
        response.say("Sorry we missed your call. Please try again later.")
        return Response(content=str(response), media_type="application/xml")

    # Check for existing active conversation (dedup)
    existing_convo = await get_active_conversation(
        business_id=business.id,
        phone=caller_phone
    )

    if not existing_convo:
        # Create new lead and conversation
        lead = await create_or_get_lead(
            business_id=business.id,
            phone=caller_phone,
            source="missed_call"
        )

        conversation = await create_conversation(
            business_id=business.id,
            lead_id=lead.id,
            call_id=call.id
        )

        # Send initial SMS
        greeting = business.ai_greeting or (
            f"Hey! Sorry we missed your call. This is {business.name}. "
            f"How can we help you today?"
        )

        await send_sms(
            to=caller_phone,
            from_=business.twilio_number,
            body=greeting,
            conversation_id=conversation.id,
            business_id=business.id
        )

        # Schedule follow-up if no reply in 2 hours
        await schedule_follow_up(
            conversation_id=conversation.id,
            delay_minutes=120
        )

        # Notify business owner
        await notify_owner(
            business=business,
            event="missed_call",
            data={
                "caller_phone": caller_phone,
                "time": datetime.utcnow().isoformat(),
                "after_hours": call.is_after_hours
            }
        )

    # Play a brief message to the caller before hanging up
    response = VoiceResponse()
    response.say(
        f"Sorry we can't take your call right now. "
        f"We'll text you right away to help. Thanks for calling {business.name}!"
    )

    return Response(content=str(response), media_type="application/xml")
```

### SMS Webhook: Incoming Message

```python
@app.post("/webhook/sms/incoming")
async def sms_incoming(request: Request):
    """
    Handles all incoming SMS messages.
    Matches to existing conversation or creates new one.
    """
    form = await request.form()
    from_number = form.get("From")
    to_number = form.get("To")
    body = form.get("Body", "").strip()

    business = await get_business_by_twilio_number(to_number)
    if not business:
        return Response(status_code=200)

    # === TCPA COMPLIANCE: Check for opt-out keywords ===
    if body.upper() in ["STOP", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"]:
        await handle_opt_out(from_number, business.id)
        # Twilio automatically handles STOP for short codes,
        # but for 10DLC we should also respond
        response = MessagingResponse()
        response.message(
            f"You've been unsubscribed from {business.name} messages. "
            f"Reply START to re-subscribe."
        )
        return Response(content=str(response), media_type="application/xml")

    if body.upper() in ["START", "YES", "UNSTOP"]:
        await handle_opt_in(from_number, business.id)
        response = MessagingResponse()
        response.message(
            f"Welcome back! You'll now receive messages from {business.name}."
        )
        return Response(content=str(response), media_type="application/xml")

    # Find active conversation
    conversation = await get_active_conversation(
        business_id=business.id,
        phone=from_number
    )

    if not conversation:
        # New inbound text without a prior missed call
        lead = await create_or_get_lead(
            business_id=business.id,
            phone=from_number,
            source="manual"
        )
        conversation = await create_conversation(
            business_id=business.id,
            lead_id=lead.id
        )

    # Save inbound message
    await save_message(
        conversation_id=conversation.id,
        business_id=business.id,
        direction="inbound",
        sender_type="caller",
        body=body,
        twilio_message_sid=form.get("MessageSid")
    )

    # Cancel any pending follow-ups
    await cancel_pending_follow_ups(conversation.id)

    # If human has taken over, don't use AI — just notify the owner
    if conversation.status == "human_active":
        await notify_owner(
            business=business,
            event="new_message",
            data={"from": from_number, "body": body}
        )
        return Response(status_code=200)

    # === AI RESPONSE ===
    ai_response = await generate_ai_response(
        conversation=conversation,
        business=business,
        new_message=body
    )

    # Send AI response
    await send_sms(
        to=from_number,
        from_=business.twilio_number,
        body=ai_response,
        conversation_id=conversation.id,
        business_id=business.id
    )

    # Schedule follow-up if no reply in 2 hours
    await schedule_follow_up(
        conversation_id=conversation.id,
        delay_minutes=120
    )

    return Response(status_code=200)
```

### A2P 10DLC Registration (REQUIRED for SMS)

**You must register for 10DLC before sending any business SMS.** Without registration, carrier filtering will block 30-80% of your messages.

Steps:
1. Register your business as a **Brand** with The Campaign Registry (TCR) via Twilio Console
2. Register a **Campaign** (use case type: "Customer Care" or "Mixed") describing your messaging
3. Each client's Twilio number gets associated with your campaign
4. Approval takes 1-5 business days
5. Once approved, throughput increases from 1 SMS/sec to 15-75 SMS/sec depending on trust score

**For MVP:** Register your own business as the Brand. Register one Campaign covering "missed call follow-up and appointment booking for service businesses." All client numbers go under this single campaign.

**At scale:** Each HVAC client may need their own Brand registration (Sole Proprietor brand) for higher throughput and better deliverability.

---

## 8. AI Conversation Engine

### System Prompt

This is the most important piece of the entire system. The AI's behavior, tone, and qualification flow all come from this prompt.

```python
def build_system_prompt(business: Business, lead: Lead, conversation: Conversation) -> str:
    """
    Build the system prompt for the AI conversation.
    This runs on every inbound message.
    """
    current_time = datetime.now(pytz.timezone(business.timezone))
    is_business_hours = check_business_hours(business, current_time)
    day_of_week = current_time.strftime("%A")

    return f"""You are a helpful, friendly assistant for {business.name}, an HVAC company.

CRITICAL RULES:
- You are NOT an AI chatbot. You are a helpful team member at {business.name}.
- Never say you are an AI, a bot, a virtual assistant, or automated.
- Never say "I'm sorry, I'm just a text-based assistant" or anything similar.
- Keep messages SHORT. 1-3 sentences max. These are SMS texts, not emails.
- Be warm, professional, and conversational. Use casual but professional language.
- Use the customer's name once you learn it.
- Never make up information. If you don't know something, say "Let me check on that and get back to you" and flag for human takeover.
- Never discuss pricing, give estimates, or promise specific costs.
- Never diagnose problems. You can acknowledge what they describe but don't suggest causes.

YOUR JOB:
You're following up after a missed call. Your goal is to:
1. Find out what they need (what HVAC service/problem)
2. Understand urgency (emergency vs can wait)
3. Get their name
4. Get the service address
5. Offer to schedule an appointment

QUALIFICATION FLOW (gather in this order, naturally):
1. Service needed — "What's going on with your [heating/AC/system]?"
2. Urgency — Is this an emergency? How long has it been happening?
3. Name — "And what's your name so I can get you in our system?"
4. Address — "What's the address for the service?"
5. Preferred time — "When works best for you? We have availability [today/tomorrow/this week]."

BUSINESS INFORMATION:
- Company: {business.name}
- Services offered: {', '.join(business.services)}
- Business hours: {json.dumps(business.business_hours)}
- Current time: {current_time.strftime('%I:%M %p')} on {day_of_week}
- Currently: {"within business hours" if is_business_hours else "after hours"}

{f"ADDITIONAL INSTRUCTIONS FROM BUSINESS: {business.ai_instructions}" if business.ai_instructions else ""}

WHAT WE KNOW ABOUT THIS LEAD SO FAR:
- Name: {lead.name or "Unknown"}
- Service needed: {lead.service_needed or "Unknown"}
- Urgency: {lead.urgency or "Unknown"}
- Address: {lead.address or "Unknown"}

WHEN THE LEAD IS QUALIFIED (you have service needed, name, address, and preferred time):
End your message with the exact string: [QUALIFIED]
This signals the system to notify the business owner and attempt booking.

IF THE CALLER SEEMS UPSET OR HAS A COMPLEX ISSUE:
End your message with: [HUMAN_NEEDED]
This alerts the business owner to step in.

IF THIS IS AN EMERGENCY (no heat in winter, gas smell, flooding, CO detector):
Immediately say: "That sounds urgent — let me get someone on this right away."
End your message with: [EMERGENCY]

CONVERSATION STYLE:
- Match the customer's energy. If they're brief, be brief. If they're chatty, be slightly warmer.
- Don't ask more than one question at a time.
- If they answer multiple questions at once, acknowledge all of them.
- Use everyday language: "AC" not "air conditioning unit", "not cooling" not "insufficient cooling"
"""
```

### AI Response Generation

```python
async def generate_ai_response(
    conversation: Conversation,
    business: Business,
    new_message: str
) -> str:
    """
    Generate an AI response using OpenAI.
    Returns the text to send as SMS.
    """
    # Get full conversation history
    messages_history = await get_conversation_messages(conversation.id)
    lead = await get_lead(conversation.lead_id)

    # Build message array for OpenAI
    openai_messages = [
        {"role": "system", "content": build_system_prompt(business, lead, conversation)}
    ]

    for msg in messages_history:
        role = "assistant" if msg.sender_type in ("ai", "human") else "user"
        openai_messages.append({"role": role, "content": msg.body})

    # Add the new message
    openai_messages.append({"role": "user", "content": new_message})

    # Call OpenAI
    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",  # Fast, cheap, excellent for SMS conversations
        messages=openai_messages,
        max_tokens=200,        # SMS should be short
        temperature=0.7,       # Slightly creative but consistent
    )

    ai_text = response.choices[0].message.content.strip()

    # Check for qualification signals
    if "[QUALIFIED]" in ai_text:
        ai_text = ai_text.replace("[QUALIFIED]", "").strip()
        await handle_qualified_lead(conversation, lead, business)

    if "[HUMAN_NEEDED]" in ai_text:
        ai_text = ai_text.replace("[HUMAN_NEEDED]", "").strip()
        await request_human_takeover(conversation, business)

    if "[EMERGENCY]" in ai_text:
        ai_text = ai_text.replace("[EMERGENCY]", "").strip()
        await handle_emergency(conversation, lead, business)

    # Extract and save any qualification data from the conversation
    await extract_qualification_data(conversation, lead, openai_messages)

    return ai_text
```

### Qualification Data Extraction

```python
async def extract_qualification_data(
    conversation: Conversation,
    lead: Lead,
    messages: list
) -> None:
    """
    After each AI response, extract structured data from the conversation.
    Uses a separate, focused API call with function calling.
    Only runs if we're missing qualification data.
    """
    if lead.name and lead.service_needed and lead.address and lead.urgency:
        return  # Already fully qualified

    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Extract customer information from this conversation. Return only what is explicitly stated."},
            {"role": "user", "content": format_conversation_for_extraction(messages)}
        ],
        tools=[{
            "type": "function",
            "function": {
                "name": "update_lead_info",
                "description": "Update lead information based on conversation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Customer's name"},
                        "service_needed": {"type": "string", "description": "What HVAC service they need"},
                        "urgency": {"type": "string", "enum": ["emergency", "soon", "flexible", "unknown"]},
                        "address": {"type": "string", "description": "Service address"},
                        "preferred_time": {"type": "string", "description": "When they want service"}
                    }
                }
            }
        }],
        tool_choice={"type": "function", "function": {"name": "update_lead_info"}}
    )

    if response.choices[0].message.tool_calls:
        data = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
        # Update lead with any new information (don't overwrite existing)
        update_fields = {}
        if data.get("name") and not lead.name:
            update_fields["name"] = data["name"]
        if data.get("service_needed") and not lead.service_needed:
            update_fields["service_needed"] = data["service_needed"]
        if data.get("urgency") and lead.urgency == "unknown":
            update_fields["urgency"] = data["urgency"]
        if data.get("address") and not lead.address:
            update_fields["address"] = data["address"]

        if update_fields:
            await update_lead(lead.id, **update_fields)
```

### Token Cost Optimization

At GPT-4o-mini pricing ($0.15/1M input, $0.60/1M output):
- Average SMS conversation: 8 messages, ~2,000 tokens total
- Cost per conversation: ~$0.001–$0.003
- Qualification extraction: ~500 tokens, ~$0.0005
- **Total AI cost per lead: ~$0.002–$0.004**
- **At 100 leads/month across all clients: ~$0.20–$0.40/month**

This is negligible. Do not optimize tokens at the MVP stage.

---

## 9. Appointment Booking

### MVP: Simple Time Slot Booking

For the MVP, don't integrate with external calendars. Use a simple internal booking system.

```python
# When AI qualifies a lead and gets a preferred time:

async def offer_booking(conversation, lead, business):
    """
    Offer available time slots to the qualified lead.
    """
    preferred = lead.qualification_data.get("preferred_time", "")

    # Get available slots for the next 3 business days
    slots = await get_available_slots(business.id, days_ahead=3)

    if not slots:
        # No automated booking — just notify owner
        await notify_owner(business, "qualified_lead", {
            "lead": lead,
            "preferred_time": preferred
        })
        return "Great, I've got all your info! Someone from our team will call you shortly to confirm a time."

    # Format slots for SMS
    slot_text = format_slots_for_sms(slots[:4])  # Max 4 options

    return (
        f"Awesome, we'd love to get you scheduled! "
        f"Here are some openings:\n\n{slot_text}\n\n"
        f"Which works best, or is there another time you'd prefer?"
    )
```

### Phase 2: Google Calendar Integration

```python
# Google Calendar integration for businesses that use it
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

async def check_google_calendar_availability(business_id: str, date: str):
    """Check a business's Google Calendar for open slots."""
    creds = await get_business_google_creds(business_id)
    service = build("calendar", "v3", credentials=creds)

    # Query freebusy
    body = {
        "timeMin": f"{date}T08:00:00Z",
        "timeMax": f"{date}T18:00:00Z",
        "items": [{"id": "primary"}]
    }
    result = service.freebusy().query(body=body).execute()

    busy_periods = result["calendars"]["primary"]["busy"]
    # Calculate free slots between busy periods
    return calculate_free_slots(busy_periods, business_hours)
```

### Phase 2+: CRM Integration

- **ServiceTitan:** Has an API but requires marketplace certification. Apply early — the approval process takes weeks to months. API supports creating jobs, customers, and bookings.
- **Housecall Pro:** Public REST API available on MAX plan. Supports creating customers, jobs, and reading schedules.
- **Jobber:** API available via partner program. Supports quotes, jobs, clients, and scheduling.

For MVP, skip CRM integration entirely. The notification to the business owner is sufficient — they can manually enter the booking into their existing system.

---

## 10. Notification System

### Real-Time Owner Notifications

```python
async def notify_owner(business: Business, event: str, data: dict):
    """
    Send notification to business owner based on their preferences.
    Respects quiet hours.
    """
    prefs = business.notification_prefs
    now = datetime.now(pytz.timezone(business.timezone))

    # Check quiet hours
    quiet_start = parse_time(prefs.get("quiet_start", "21:00"))
    quiet_end = parse_time(prefs.get("quiet_end", "07:00"))
    in_quiet_hours = is_in_quiet_hours(now.time(), quiet_start, quiet_end)

    # Build notification message based on event type
    message = build_notification_message(event, data, business)

    # SMS notification (unless quiet hours)
    if prefs.get("sms", True) and not in_quiet_hours:
        await twilio_client.messages.create(
            to=business.owner_phone,
            from_=business.twilio_number,  # From their own number
            body=message
        )

    # Email notification (always, for record)
    if prefs.get("email", True):
        await send_email(
            to=business.owner_email,
            subject=build_email_subject(event, data),
            body=message
        )

    # Dashboard real-time update (Supabase Realtime)
    await supabase.table("notifications").insert({
        "business_id": str(business.id),
        "event": event,
        "data": data,
        "read": False,
        "created_at": datetime.utcnow().isoformat()
    }).execute()


def build_notification_message(event: str, data: dict, business: Business) -> str:
    """Build human-readable notification messages."""
    templates = {
        "missed_call": (
            f"📞 Missed call from {format_phone(data['caller_phone'])} "
            f"at {format_time(data['time'], business.timezone)}. "
            f"AI is following up now."
        ),
        "qualified_lead": (
            f"🔥 New qualified lead!\n"
            f"Name: {data['lead'].name or 'Unknown'}\n"
            f"Needs: {data['lead'].service_needed}\n"
            f"Urgency: {data['lead'].urgency}\n"
            f"Address: {data['lead'].address or 'Not provided'}\n"
            f"Phone: {format_phone(data['lead'].phone)}"
        ),
        "appointment_booked": (
            f"✅ Appointment booked!\n"
            f"{data['lead'].name} - {data['appointment'].service_type}\n"
            f"{data['appointment'].scheduled_date} at {data['appointment'].scheduled_time}\n"
            f"{data['appointment'].address}"
        ),
        "emergency": (
            f"🚨 EMERGENCY lead!\n"
            f"{data['lead'].name or 'Unknown'} at {data['lead'].address or 'unknown address'}\n"
            f"Issue: {data['lead'].service_needed}\n"
            f"Phone: {format_phone(data['lead'].phone)}\n"
            f"CALL THEM IMMEDIATELY"
        ),
        "human_needed": (
            f"⚠️ AI needs help with a conversation.\n"
            f"Customer: {format_phone(data['lead'].phone)}\n"
            f"Please check the dashboard and take over."
        )
    }
    return templates.get(event, f"Notification: {event}")
```

---

## 11. Review Request Automation

### Flow

```
1. Business marks a job as "completed" (via dashboard or API)
   │
2. Wait 2 hours (let them finish cleanup, drive home)
   │
3. Send review request SMS:
   "Hi [Name]! Thanks for choosing [Business Name] today.
    If you had a great experience, would you mind leaving us
    a quick Google review? It really helps!
    [Review Link]"
   │
4. If no review after 48 hours, send one reminder:
   "Hey [Name], just a friendly reminder — if you have 30 seconds,
    a Google review would mean the world to us!
    [Review Link]
    Thanks! - [Business Name]"
   │
5. Never send more than one reminder. Mark as complete regardless.
```

### Google Review Direct Link

```python
def get_google_review_link(place_id: str) -> str:
    """
    Generate a direct link to leave a Google review.
    The place_id comes from Google Places API or can be found
    at https://developers.google.com/maps/documentation/places/web-service/place-id
    """
    return f"https://search.google.com/local/writereview?placeid={place_id}"
```

**During onboarding**, look up the client's Google Place ID and store it in the `businesses` table. This is a one-time manual step.

---

## 12. Dashboard & Frontend

### Dashboard Pages

```
/login              - Magic link email login
/dashboard          - Overview: today's stats, recent activity, quick actions
/calls              - Call log with filters (all, missed, answered, date range)
/leads              - Lead pipeline view (new, qualifying, qualified, booked)
/leads/[id]         - Lead detail: full conversation, timeline, actions
/conversations      - Active conversations with takeover option
/appointments       - Appointment calendar/list view
/reports            - Weekly/monthly reports with ROI calculation
/settings           - Business hours, AI greeting, notification prefs, billing
```

### Key Dashboard Metrics (Home Page)

```
┌──────────────────────────────────────────────────────────────┐
│  TODAY                                                        │
│                                                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────────┐   │
│  │ 12      │  │ 4       │  │ 3       │  │ $1,050       │   │
│  │ Calls   │  │ Missed  │  │ Recovered│  │ Est. Revenue │   │
│  └─────────┘  └─────────┘  └─────────┘  └──────────────┘   │
│                                                               │
│  THIS MONTH                                                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────────┐   │
│  │ 284     │  │ 89      │  │ 62      │  │ $21,700      │   │
│  │ Calls   │  │ Missed  │  │ Recovered│  │ Est. Revenue │   │
│  └─────────┘  └─────────┘  └─────────┘  └──────────────┘   │
│                                                               │
│  RECENT ACTIVITY                                              │
│  ● 2:34 PM  Missed call from (555) 123-4567 — AI following up│
│  ● 2:21 PM  Lead qualified: Sarah M. — AC not cooling        │
│  ● 1:45 PM  Appointment booked: Tom R. — Tomorrow 10am       │
│  ● 12:30 PM Review received: ★★★★★ from Mike D.             │
└──────────────────────────────────────────────────────────────┘
```

### Conversation View with Takeover

```
┌──────────────────────────────────────────────────────────────┐
│  Conversation with (555) 123-4567                             │
│  Lead: Sarah Martinez | Status: Qualifying                    │
│  Started: Today 2:34 PM (missed call)                         │
│                                                               │
│  [AI] Hey! Sorry we missed your call. This is Smith's         │
│       Heating & Air. How can we help you today?               │
│                                                   2:34 PM     │
│                                                               │
│  [Customer] Hi yeah my AC isn't blowing cold air              │
│                                                   2:36 PM     │
│                                                               │
│  [AI] Sorry to hear that! How long has it been going on?      │
│       Is it completely warm air or just not as cold as usual?  │
│                                                   2:36 PM     │
│                                                               │
│  [Customer] Since this morning. It's blowing but not cold     │
│                                                   2:38 PM     │
│                                                               │
│  [AI] Got it. And what's your name so I can get you in our    │
│       system?                                                  │
│                                                   2:38 PM     │
│                                                               │
│  ┌────────────────────┐  ┌────────────────────────────────┐  │
│  │  🤖 AI is handling │  │  [Take Over Conversation]      │  │
│  └────────────────────┘  └────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────┐ ┌──────────────┐   │
│  │ Type a message...                    │ │    Send       │   │
│  └──────────────────────────────────────┘ └──────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Tech Implementation

```
Frontend:
- Next.js 14+ with App Router
- Tailwind CSS + shadcn/ui components
- TanStack Query for data fetching
- Supabase Realtime for live updates
- Recharts for metric visualization
- Date-fns for time formatting (respect business timezone)

Key patterns:
- Server components for initial page loads
- Client components for interactive elements (conversations, filters)
- Supabase Realtime subscription for live conversation updates
- Optimistic UI updates when owner sends a message
- Mobile-responsive (owners check on phones constantly)
```

---

## 13. Authentication & Multi-Tenancy

### Auth Flow

```
1. Owner enters email on login page
2. Server sends magic link via Supabase Auth
3. Owner clicks link, gets JWT
4. JWT contains user_id → maps to business_id
5. All API requests include JWT in Authorization header
6. Backend middleware extracts business_id from JWT
7. ALL database queries are scoped to that business_id
```

### Multi-Tenancy Security

```python
# Middleware that runs on every API request
async def get_current_business(request: Request) -> Business:
    """
    Extract business from JWT. ALL downstream queries use this.
    Never trust business_id from request parameters.
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = supabase.auth.get_user(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    business = await get_business_by_user_id(user.id)

    if not business:
        raise HTTPException(status_code=403, detail="No business associated")

    return business


# Example of scoped query — EVERY query follows this pattern
async def get_leads(business_id: UUID, status: str = None):
    query = select(Lead).where(Lead.business_id == business_id)
    if status:
        query = query.where(Lead.status == status)
    return await db.execute(query)
```

### Admin Access (Your Internal Dashboard)

Separate auth flow for you (the system admin) to manage all businesses:
- Separate admin table with role-based access
- Admin JWT includes `is_admin=True` flag
- Admin endpoints bypass business_id scoping
- Used for onboarding, monitoring, billing management

---

## 14. Compliance & Legal

### TCPA Compliance (Critical)

The Telephone Consumer Protection Act governs automated text messages. Violations carry **$500–$1,500 per message** in penalties.

**For missed call text-back (your core product):**
- When a person calls a business, they are initiating contact
- Responding to that call (even via SMS) is generally considered permissible as a "transactional" response
- However, this is a gray area — you're sending an automated text, not a human response
- **Best practice:** Include opt-out instructions in the first message and honor STOP immediately

**Required for all SMS:**
1. **Honor STOP keywords instantly** — STOP, UNSUBSCRIBE, CANCEL, END, QUIT
2. **Include business identification** — the business name in every first message
3. **No messages to opted-out numbers** — check opt-out table before every send
4. **Maintain opt-out records** — keep indefinitely

**For follow-up sequences (the 2hr, 24hr, 72hr follow-ups):**
- These are more clearly "marketing" in nature
- The initial call provides implied consent for reasonable follow-up
- Keep it to 3 messages maximum
- Always include opt-out option
- Stop immediately on STOP or any negative response

**For review requests:**
- Requires prior express consent (they were your customer)
- Limit to 1 request + 1 reminder
- Include opt-out

**For database reactivation (Phase 3):**
- Requires **prior express written consent** for marketing messages
- The business must have obtained consent when the customer's number was collected
- You must have records of this consent
- This is the highest-risk area — implement carefully

### A2P 10DLC Registration

All business SMS in the US must go through 10DLC registration as of 2024. Without it:
- Messages get filtered/blocked by carriers (30-80% failure rate)
- Throughput is limited to 1 SMS/second
- You may get your Twilio account suspended

**Registration steps:**
1. Create a Twilio Brand (your business entity) — $4 one-time
2. Create a Campaign (message use case) — $15/month
3. Associate phone numbers with the campaign
4. Wait 1-5 business days for approval

### Call Recording Consent

If you record calls or voicemails:
- **11 states require two-party consent**: California, Connecticut, Florida, Illinois, Maryland, Massachusetts, Michigan, Montana, New Hampshire, Pennsylvania, Washington
- The TwiML `<Say>` message before connecting ("This call may be recorded...") covers this
- For MVP, you're not recording calls — you're just detecting missed calls

### Data Privacy

- Store phone numbers and conversation data encrypted at rest (Supabase does this by default)
- Never expose raw phone numbers in logs or error messages
- Implement data retention policy (suggest: 2 years, then anonymize)
- Provide data export/deletion on request (CCPA compliance)

---

## 15. Infrastructure & Deployment

### Docker Setup

```dockerfile
# Dockerfile for the backend
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml for local development
version: "3.8"

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - redis
    volumes:
      - ./backend:/app

  worker:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    env_file:
      - .env
    depends_on:
      - redis

  scheduler:
    build: ./backend
    command: celery -A app.worker beat --loglevel=info
    env_file:
      - .env
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
```

### Environment Variables

```bash
# .env.example
# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Supabase
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DATABASE_URL=postgresql://postgres:xxx@db.xxxxxxxxxxxxx.supabase.co:5432/postgres

# Redis
REDIS_URL=redis://localhost:6379/0

# App
BASE_URL=https://yourdomain.com  # Your server's public URL (use ngrok for dev)
ENVIRONMENT=development           # development | staging | production

# Email (Resend)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Stripe (billing)
STRIPE_SECRET_KEY=sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Project Structure

```
hvac-ai-recovery/
├── README.md
├── LICENSE                    # AGPL-3.0
├── docker-compose.yml
├── .env.example
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/               # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── main.py            # FastAPI app entry
│   │   ├── config.py          # Settings from env vars
│   │   ├── database.py        # SQLAlchemy setup
│   │   │
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── business.py
│   │   │   ├── call.py
│   │   │   ├── lead.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   ├── appointment.py
│   │   │   └── review_request.py
│   │   │
│   │   ├── api/               # API routes
│   │   │   ├── webhooks/      # Twilio webhooks
│   │   │   │   ├── voice.py
│   │   │   │   └── sms.py
│   │   │   ├── dashboard.py
│   │   │   ├── leads.py
│   │   │   ├── conversations.py
│   │   │   ├── appointments.py
│   │   │   ├── reports.py
│   │   │   ├── settings.py
│   │   │   └── admin.py
│   │   │
│   │   ├── services/          # Business logic
│   │   │   ├── ai_engine.py   # OpenAI integration
│   │   │   ├── sms.py         # Twilio SMS helpers
│   │   │   ├── voice.py       # Twilio Voice helpers
│   │   │   ├── notifications.py
│   │   │   ├── booking.py
│   │   │   ├── reviews.py
│   │   │   ├── follow_up.py
│   │   │   └── metrics.py
│   │   │
│   │   ├── worker/            # Celery tasks
│   │   │   ├── tasks.py       # Follow-ups, reports, campaigns
│   │   │   └── schedules.py   # Periodic task schedule
│   │   │
│   │   └── middleware/
│   │       ├── auth.py        # JWT validation
│   │       └── tenant.py      # Business scoping
│   │
│   └── tests/
│       ├── test_webhooks.py
│       ├── test_ai_engine.py
│       └── test_flows.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx           # Login
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx       # Main dashboard
│   │   │   ├── calls/
│   │   │   │   └── page.tsx
│   │   │   ├── leads/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── conversations/
│   │   │   │   └── page.tsx
│   │   │   ├── appointments/
│   │   │   │   └── page.tsx
│   │   │   ├── reports/
│   │   │   │   └── page.tsx
│   │   │   └── settings/
│   │   │       └── page.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                # shadcn components
│   │   │   ├── dashboard/
│   │   │   ├── conversation/
│   │   │   └── layout/
│   │   │
│   │   └── lib/
│   │       ├── supabase.ts
│   │       ├── api.ts
│   │       └── utils.ts
│   │
│   └── public/
│
└── docs/                          # For open-source
    ├── setup.md
    ├── configuration.md
    ├── deployment.md
    ├── api-reference.md
    └── contributing.md
```

### Deployment (Production)

**Backend:** Deploy to Railway ($5/mo hobby, $20/mo pro) or Render
- Set environment variables
- Railway auto-deploys from GitHub pushes
- Use Railway's built-in Redis addon

**Frontend:** Deploy to Vercel (free tier is sufficient)
- Connect GitHub repo
- Auto-deploys on push

**Database:** Supabase (free tier for development, $25/mo for production)
- Enable Row Level Security for all tables
- Set up database backups

**Domain:** Point your domain to Vercel (frontend) and Railway (backend API)
- api.yourdomain.com → Railway
- app.yourdomain.com → Vercel

### Monitoring

```
- Sentry (free tier): Error tracking for backend + frontend
- Uptime Robot (free tier): Uptime monitoring for webhook endpoints
- Supabase Dashboard: Database monitoring
- Twilio Console: SMS delivery rates, call logs
- Custom: Daily email report with key metrics across all clients
```

---

## 16. Phase 2: Voice AI

### When to Build This

Build voice AI AFTER you have 3-5 paying clients on the SMS-only system. Voice AI:
- Justifies a price increase ($497 → $797/mo)
- Creates a genuine technical moat (GHL can't do this)
- Dramatically improves the customer experience

### Architecture Options

**Option A: Vapi.ai (recommended for MVP)**
- Fully managed voice AI platform
- $0.05/minute all-in
- Handles STT → LLM → TTS pipeline
- Twilio integration built-in
- Fastest to deploy (days, not weeks)
- Downside: dependency on third party, less customizable

**Option B: Custom Pipeline (recommended for scale)**
- Twilio Voice → Deepgram STT → OpenAI → ElevenLabs/Deepgram TTS → Twilio Voice
- More control, lower cost at scale (~$0.02-0.03/minute)
- Significant engineering effort (2-4 weeks)
- Better for customization and open-sourcing

**Recommended path:**
1. Launch Voice AI with Vapi.ai for speed
2. Build custom pipeline in parallel
3. Migrate to custom when volume justifies it

### Voice AI Call Flow

```
1. Call comes in → ring HVAC phone for 20 seconds
2. No answer → instead of voicemail, connect to Voice AI
3. Voice AI: "Hi! Thanks for calling [Business Name].
   Sorry nobody could get to the phone.
   I can help you out — what do you need today?"
4. Caller describes issue verbally
5. AI qualifies (same logic as SMS, but spoken)
6. AI attempts to book appointment
7. AI: "Great, I've got you down for tomorrow at 2pm.
   Someone from our team will confirm shortly.
   Is there anything else I can help with?"
8. Call ends → notification to owner with full transcript
```

---

## 17. Phase 3: Database Reactivation

### When to Build This

After 5-10 clients are stable on the core product. This becomes an upsell.

### Flow

```
1. HVAC company exports past customer list (CSV)
2. You import into the system
3. System sends personalized campaigns:
   - Seasonal maintenance reminders
   - "We haven't heard from you in a while" re-engagement
   - Special offer campaigns
4. Responses feed into the same AI conversation engine
5. Qualified leads get booked like any other
```

### TCPA Warning

Database reactivation requires **prior express written consent** for marketing SMS. The HVAC company must confirm they collected these phone numbers with proper consent. Add a checkbox during import: "I confirm these contacts opted in to receive marketing messages from my business."

---

## 18. Cost Model

### Per-Client Monthly Costs

| Item | Low Usage | Medium Usage | High Usage |
|------|----------|-------------|-----------|
| Twilio phone number | $1.15 | $1.15 | $1.15 |
| Twilio SMS (~50-200 msgs) | $0.40 | $1.70 | $3.40 |
| Twilio Voice (forwarding, ~200-500 min) | $2.80 | $7.00 | $14.00 |
| OpenAI GPT-4o-mini | $0.01 | $0.05 | $0.15 |
| **Subtotal per client** | **$4.36** | **$9.90** | **$18.70** |

### Platform Fixed Costs

| Item | Monthly Cost |
|------|-------------|
| Supabase Pro | $25 |
| Railway (backend) | $20 |
| Vercel (frontend) | $0–20 |
| Redis | $0–5 |
| Resend (email) | $0–20 |
| Sentry | $0 |
| Domain + SSL | ~$2 |
| **Total fixed** | **$47–92/month** |

### Margin Analysis

At $497/month per client with medium usage:
- COGS per client: ~$10/mo
- Platform cost allocation (at 10 clients): ~$7/mo per client
- **Gross margin per client: ~$480/mo (96.6%)**
- **At 15 clients: $7,455/mo revenue, ~$240/mo total COGS = 96.8% margin**

---

## 19. Open-Source Considerations

### License

Use **AGPL-3.0**. This means:
- Anyone can self-host for free
- Anyone who modifies and deploys it must share their changes
- Companies wanting to use it without sharing changes need a commercial license (from you)
- This is the same license used by MongoDB, Grafana, and n8n

### What to Open-Source

- The entire codebase (backend + frontend)
- Docker Compose for one-command deployment
- Full documentation
- Example configurations for HVAC and other verticals

### What to Keep Proprietary (Optional Premium Features)

- White-label/multi-tenant management console
- Advanced analytics and reporting
- Priority support and SLA
- Pre-built CRM integrations (ServiceTitan, Housecall Pro)
- Voice AI module (initially)

### README Structure

```markdown
# 🔧 CallRecover — AI-Powered Missed Call Recovery for Service Businesses

> Turn every missed call into a booked job. Open-source.

CallRecover automatically texts back missed callers, qualifies leads through
AI-powered SMS conversations, and books appointments — so you never lose
a job to a competitor again.

Built for HVAC, plumbing, electrical, and other service businesses.

## Quick Start

\`\`\`bash
git clone https://github.com/yourusername/callrecover.git
cd callrecover
cp .env.example .env  # Add your API keys
docker compose up
\`\`\`

Visit http://localhost:3000 to set up your first business.

## Features

- 📞 Missed call detection via Twilio
- 💬 AI-powered SMS conversations (OpenAI)
- 📅 Appointment booking
- ⭐ Automated review requests
- 📊 Real-time dashboard
- 🔔 Owner notifications (SMS + email)
- 🏢 Multi-tenant (manage multiple businesses)

## Documentation

- [Setup Guide](docs/setup.md)
- [Configuration](docs/configuration.md)
- [Deployment](docs/deployment.md)
- [API Reference](docs/api-reference.md)

## Don't want to self-host?

We offer a fully managed version at [yourwebsite.com](https://yourwebsite.com).
Setup in 24 hours, no technical skills required.

## License

AGPL-3.0. See [LICENSE](LICENSE) for details.
Commercial licenses available — contact us at hello@yourwebsite.com.
```

---

## 20. Build Sequence

### Week 1: Core Backend + Missed Call → SMS Flow

**Day 1-2:**
- Set up project structure (backend + frontend repos)
- Configure Supabase project + database schema
- Set up Twilio account + buy first test number
- Implement environment config

**Day 3-4:**
- Build Twilio voice webhook (incoming call → dial → detect missed)
- Build Twilio SMS webhook (send/receive messages)
- Implement conversation threading (match inbound SMS to conversations)
- Test: call your Twilio number → don't answer → receive text-back

**Day 5:**
- Integrate OpenAI for AI responses
- Build system prompt with HVAC qualification flow
- Implement qualification data extraction
- Test: full conversation flow from missed call to qualified lead

**Day 6-7:**
- Build follow-up sequence (2hr → 24hr → 72hr)
- Implement STOP/opt-out handling
- Add basic error handling and logging
- End-to-end test with a real phone

### Week 2: Notifications + Dashboard + Booking

**Day 8-9:**
- Build notification system (SMS + email to owner)
- Implement real-time notifications via Supabase
- Build human takeover flow

**Day 10-12:**
- Build Next.js dashboard: login, main stats, call log, lead list
- Build conversation view with takeover button
- Build settings page
- Connect to Supabase Realtime for live updates

**Day 13-14:**
- Build simple appointment booking flow
- Build daily metrics computation
- Build weekly/monthly report generation
- Polish UI, fix bugs, test all flows

### Week 3: Production Readiness + First Client

**Day 15-16:**
- Dockerize everything
- Deploy backend to Railway
- Deploy frontend to Vercel
- Set up Sentry error tracking
- A2P 10DLC registration

**Day 17-18:**
- Build admin dashboard for managing businesses
- Build client onboarding flow (provision number, configure business)
- Set up Stripe billing integration
- Write onboarding documentation

**Day 19-21:**
- Comprehensive testing with multiple test businesses
- Load testing (simulate 50+ concurrent conversations)
- Security review (auth, injection, rate limiting)
- Onboard first beta client

---

## Appendix: Key Technical Decisions

### Why FastAPI over Express/Node.js?
- Python has the best AI/ML ecosystem (OpenAI SDK, LangChain if needed)
- FastAPI's async support handles webhook concurrency well
- Type hints + Pydantic provide runtime validation for webhook payloads
- Auto-generated API docs speed up frontend development

### Why Supabase over raw PostgreSQL?
- Built-in auth (magic links, JWT) eliminates weeks of auth work
- Realtime subscriptions for live dashboard updates
- Generous free tier for development
- Row Level Security for multi-tenant data isolation
- Easy migration to self-hosted Supabase for open-source users

### Why GPT-4o-mini over GPT-4o?
- SMS conversations are short and simple — mini handles them perfectly
- 10-15x cheaper than GPT-4o
- Faster response times (lower latency = faster SMS back to caller)
- Use GPT-4o only for voice AI (Phase 2) where quality matters more

### Why Celery over simple cron jobs?
- Follow-up sequences need precise timing (2hr, 24hr, 72hr delays)
- Retry logic for failed SMS sends
- Rate limiting for bulk operations (review requests, reactivation)
- Can scale workers independently when volume grows

### Why not GoHighLevel or other no-code platforms?
- You're building a product, not a service configuration
- GHL takes 30-40% margin and limits customization
- Can't open-source a GHL setup
- Voice AI is impossible on GHL
- Your coding ability IS the competitive advantage — use it
