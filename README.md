# CallHook — AI Voice Receptionist for Service Businesses

Every call answered. Every lead captured. No job lost to a competitor.

When an HVAC company misses a call, CallHook's voice AI answers it — talks to the customer, qualifies the lead, and books the appointment before they hang up and call someone else.

Built for HVAC, plumbing, electrical, and home service businesses. Open-source.

## How It Works

1. Customer calls your business number
2. Your phone rings for 20 seconds — if your team picks up, the call connects normally and CallHook stays invisible
3. If nobody answers, CallHook's voice AI picks up the call seamlessly
4. The AI has a natural phone conversation: finds out what they need, gets their name and address, and offers to schedule service
5. You get an instant notification with the qualified lead, full transcript, and call recording
6. A confirmation text goes to the caller with their booking details

The customer never knows they talked to AI. They called, someone answered, they're booked.

## Why Voice AI Instead of Text-Back?

Every other missed call tool sends a text message after the call ends. That loses 15-25% of callers (landlines, non-texters, older homeowners) and gives them time to call your competitor. CallHook answers the actual call — the customer never hangs up, never waits, never leaves.

## Features

**Voice AI (Primary)**
- AI answers missed calls with natural conversation
- Real-time lead qualification during the call (service needed, urgency, name, address, timing)
- Emergency detection — gas leaks, no heat, CO alarms trigger immediate owner alerts
- Call recording and full transcript saved
- Landline and mobile callers both handled
- Automatic fallback to SMS if voice AI is unavailable

**SMS (Secondary Channel)**
- Post-call confirmation texts to mobile callers
- Follow-up sequences for incomplete calls (caller hung up early)
- Inbound SMS handling with AI conversation engine
- TCPA-compliant opt-out (STOP/START keywords)

**Business Owner Tools**
- Real-time dashboard: calls, leads, revenue recovered, ROI
- Conversation view with transcripts, recordings, and message history
- Human takeover — jump into any conversation from the dashboard
- Owner nudges — reminders to call back qualified leads
- Automated Google review requests after completed jobs
- Weekly email reports with key metrics
- Notification preferences with quiet hours

**Platform**
- Multi-tenant: one deployment serves all your clients
- Admin panel for managing businesses, monitoring system health, tracking costs
- Stripe billing integration

## Tech Stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Celery, Redis

**Voice AI:** Vapi.ai (MVP) → Custom Twilio + Deepgram + OpenAI + ElevenLabs pipeline (scale)

**Frontend:** Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Recharts, TanStack Query

**Services:** Twilio (voice + SMS), OpenAI (GPT-4o-mini for SMS), Supabase (PostgreSQL + Auth + Realtime), Resend (email), Stripe (billing)

## Project Structure

```
hvac-ai-recovery/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routes
│   │   │   └── webhooks/    # Twilio voice, SMS, Vapi, Stripe webhooks
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── services/        # Business logic (voice AI, SMS, AI engine,
│   │   │                    #   notifications, booking, follow-ups)
│   │   ├── middleware/      # Auth + multi-tenant scoping
│   │   └── worker/          # Celery tasks (follow-ups, reports, reviews)
│   ├── alembic/             # Database migrations
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/             # Next.js pages (dashboard, leads, conversations,
│       │                    #   calls, appointments, reports, settings)
│       ├── components/      # Layout, UI components
│       ├── hooks/           # Supabase realtime subscriptions
│       └── lib/             # API client, auth, utilities
├── supabase/                # SQL scripts (RLS, realtime, auth triggers)
├── docs/                    # Architecture and implementation specs
├── docker-compose.yml
└── .env.example
```

## Quick Start

```bash
git clone https://github.com/joelbyler272/hvac-ai-recovery.git
cd hvac-ai-recovery
cp .env.example .env  # Add your API keys (see Configuration below)
docker compose up
```

Visit http://localhost:3000 to access the dashboard.

For Twilio webhooks to work locally, expose your backend with [ngrok](https://ngrok.com):

```bash
ngrok http 8000
```

Then set the ngrok URL as `BASE_URL` in your `.env`.

## Development

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- Twilio account (voice + SMS enabled)
- Vapi.ai account
- OpenAI API key
- Supabase project

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database Setup

See [supabase/SETUP.md](supabase/SETUP.md) for complete Supabase configuration including RLS policies, realtime subscriptions, and auth triggers.

### Tests

```bash
cd backend
pytest tests/ -v
```

## Configuration

See `.env.example` for all environment variables. Key settings:

| Variable | Description |
|---|---|
| `TWILIO_ACCOUNT_SID` | Twilio account credentials |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `VAPI_API_KEY` | Vapi.ai API key for voice AI |
| `OPENAI_API_KEY` | OpenAI API key (GPT-4o-mini for SMS conversations) |
| `DATABASE_URL` | PostgreSQL connection string (Supabase) |
| `SUPABASE_URL` | Supabase project URL |
| `BASE_URL` | Your server's public URL (ngrok for local dev) |
| `STRIPE_SECRET_KEY` | Stripe key for subscription billing |

## Deployment

**Backend:** Railway ($20-35/mo for API + worker + scheduler)

**Frontend:** Vercel (free tier)

**Database:** Supabase ($25/mo Pro plan)

**Total platform cost:** ~$65-85/month fixed + ~$15-25/month per client (Twilio + Vapi usage)

See [docs/implementation.md](docs/implementation.md) for the full technical specification.

## Don't want to self-host?

We offer a fully managed version at $497/month. Setup in 24 hours, no technical skills required.

## License

AGPL-3.0. See [LICENSE](LICENSE) for details.

Commercial licenses available for businesses that want to deploy without sharing modifications.
