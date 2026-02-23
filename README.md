# CallHook — AI-Powered Missed Call Recovery for Service Businesses

Turn every missed call into a booked job. Open-source.

CallHook automatically texts back missed callers, qualifies leads through AI-powered SMS conversations, and books appointments — so you never lose a job to a competitor again.

Built for HVAC, plumbing, electrical, and other service businesses.

## Quick Start

```bash
git clone https://github.com/yourusername/callhook.git
cd callhook
cp .env.example .env  # Add your API keys
docker compose up
```

Visit http://localhost:3000 to set up your first business.

## How It Works

1. Caller dials your business number
2. If nobody answers within 20 seconds, the system detects the missed call
3. An instant SMS goes to the caller: "Sorry we missed your call! How can we help?"
4. AI qualifies the lead through natural SMS conversation (service needed, urgency, name, address)
5. Business owner gets a real-time notification with all lead details
6. Lead is booked for an appointment or the owner takes over the conversation

## Features

- Missed call detection via Twilio voice webhooks
- AI-powered SMS conversations (OpenAI GPT-4o-mini)
- Lead qualification and status tracking
- Appointment booking
- Automated follow-up sequences (2hr, 24hr, 72hr)
- TCPA-compliant opt-out handling (STOP/START keywords)
- Automated Google review requests after completed jobs
- Real-time dashboard with metrics and ROI tracking
- Owner notifications (SMS + email) with quiet hours
- Human takeover — owner can jump into any conversation
- Multi-tenant — one deployment serves multiple businesses

## Tech Stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Celery, Redis

**Frontend:** Next.js 14, TypeScript, Tailwind CSS, Recharts, TanStack Query

**Services:** Twilio (voice + SMS), OpenAI (GPT-4o-mini), Supabase (PostgreSQL + Auth + Realtime), Resend (email)

## Project Structure

```
hvac-ai-recovery/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes + webhook handlers
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── services/      # Business logic (AI, SMS, notifications)
│   │   ├── middleware/     # Auth + multi-tenant scoping
│   │   └── worker/        # Celery tasks (follow-ups, reports)
│   ├── alembic/           # Database migrations
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/           # Next.js pages (dashboard, leads, etc.)
│       ├── components/    # Layout, UI components
│       ├── hooks/         # Real-time subscriptions
│       └── lib/           # API client, auth, utilities
├── docker-compose.yml
└── .env.example
```

## Development

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- Twilio account
- OpenAI API key
- Supabase project

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
cd backend
pytest tests/ -v
```

### Local Webhook Testing

Use [ngrok](https://ngrok.com) to expose your local server for Twilio webhooks:

```bash
ngrok http 8000
```

Set the ngrok URL as `BASE_URL` in your `.env` and configure Twilio webhook URLs accordingly.

## Configuration

See `.env.example` for all required environment variables. Key settings:

| Variable | Description |
|----------|-------------|
| `TWILIO_ACCOUNT_SID` | Twilio account credentials |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o-mini |
| `DATABASE_URL` | PostgreSQL connection string |
| `SUPABASE_URL` | Supabase project URL |
| `BASE_URL` | Your server's public URL |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins for production |

## Deployment

**Backend:** Railway or Render ($5-25/mo)

**Frontend:** Vercel (free tier)

**Database:** Supabase (free tier for dev, $25/mo for production)

See `docs/architecture.md` for the full technical specification.

## Don't want to self-host?

We offer a fully managed version. Setup in 24 hours, no technical skills required.

## License

AGPL-3.0. See [LICENSE](LICENSE) for details.
