from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.webhooks.voice import router as voice_router
from app.api.webhooks.sms import router as sms_router
from app.api.dashboard import router as dashboard_router
from app.api.leads import router as leads_router
from app.api.conversations import router as conversations_router
from app.api.appointments import router as appointments_router
from app.api.reports import router as reports_router
from app.api.settings import router as settings_router
from app.api.calls import router as calls_router
from app.api.admin import router as admin_router
from app.api.services import router as services_router
from app.api.calendar import router as calendar_router

settings = get_settings()

app = FastAPI(
    title="CallRecover API",
    description="AI-Powered Missed Call Recovery for Service Businesses",
    version="1.0.0",
)

# CORS — use ALLOWED_ORIGINS env var in production (comma-separated)
_default_origins = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"]
_extra = settings.allowed_origins.split(",") if getattr(settings, "allowed_origins", None) else []
_origins = _default_origins + [o.strip() for o in _extra if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Webhook routes (Twilio)
app.include_router(voice_router, prefix="/webhook/voice", tags=["Webhooks - Voice"])
app.include_router(sms_router, prefix="/webhook/sms", tags=["Webhooks - SMS"])

# Dashboard API routes
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(leads_router, prefix="/api/leads", tags=["Leads"])
app.include_router(conversations_router, prefix="/api/conversations", tags=["Conversations"])
app.include_router(appointments_router, prefix="/api/appointments", tags=["Appointments"])
app.include_router(calls_router, prefix="/api/calls", tags=["Calls"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
app.include_router(services_router, prefix="/api/services", tags=["Services"])
app.include_router(calendar_router, prefix="/api/calendar", tags=["Calendar"])

# Admin routes
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
