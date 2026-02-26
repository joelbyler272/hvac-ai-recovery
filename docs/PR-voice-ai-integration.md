# Voice AI Integration — PR Description

## Branch: `feature/voice-ai-integration`

## Summary

This PR transforms CallRecover from an SMS text-back system into a voice AI receptionist. Instead of texting callers after a missed call, CallRecover now answers the call with AI, qualifies the lead through natural conversation, and books the appointment — all before the caller hangs up.

SMS becomes a secondary channel for post-call confirmations, incomplete call recovery, review requests, and inbound text handling.

## Why This Change

The SMS-first approach had three critical weaknesses:
1. **Loses 15-25% of callers** — landline callers can't receive texts
2. **Gives callers time to call competitors** — the text arrives after they've already hung up
3. **No differentiation** — every GoHighLevel reseller offers missed call text-back

Voice AI answers the actual call. The caller never hangs up, never waits, never calls the next company on the list.

## What Changes

### New: Voice AI System
- Vapi.ai integration for voice conversation AI
- Voice AI system prompt with HVAC-specific qualification flow
- Real-time function calling for lead data extraction during calls
- Emergency detection and immediate owner alerting
- Call recording and transcript storage
- Twilio Lookup API for line type detection (mobile vs landline)
- Automatic fallback to SMS text-back if voice AI is unavailable

### New: Post-Call Processing
- Confirmation SMS to mobile callers after successful voice calls
- SMS recovery sequence for incomplete voice calls (caller hung up early)
- Owner nudge system — remind owner to call back qualified leads after 30 minutes

### New: Billing
- Stripe webhook integration for subscription lifecycle
- Service pausing on payment failure

### Modified: Call Flow
- /webhook/voice/call-completed now transfers to Voice AI instead of triggering SMS
- SMS conversation engine preserved for inbound texts and fallback scenarios

### Modified: Dashboard
- Conversation view now includes voice transcripts and audio player for recordings
- Call detail shows voice AI usage, duration, and cost

### Modified: Database
- New columns on calls, leads, conversations, businesses tables
- New tables: voice_ai_configs, owner_nudges

### Updated: Documentation
- README rewritten to reflect voice-AI-first product
- New implementation spec (docs/implementation.md) replaces v1 architecture
- .env.example updated with Vapi credentials

## Implementation Plan

Work is organized into 9 priority tiers (see docs/implementation.md Section 20):

1. **Voice AI Integration** — Vapi setup, call transfer, webhook handling
2. **Production Deployment** — Railway, Vercel, Supabase production
3. **Post-Call SMS & Recovery** — confirmations, incomplete call follow-ups
4. **Owner Nudge System** — 30-minute callback reminders
5. **Review Requests with Google Link** — direct review URLs
6. **Stripe Billing** — subscription webhooks and lifecycle
7. **Error Handling & Resilience** — fallbacks, rate limiting, validation
8. **Admin Monitoring** — health checks, cost tracking
9. **Polish & First Client** — landing page, testing, onboarding

## Testing Plan

- [ ] Call Twilio number → let it ring → voice AI answers → full qualification conversation
- [ ] Verify lead record created with all extracted data
- [ ] Verify owner notification fires within 60 seconds of call end
- [ ] Verify confirmation SMS sent to mobile callers
- [ ] Verify landline callers handled (voice only, no SMS)
- [ ] Verify emergency detection triggers priority alert
- [ ] Verify human takeover flag works during voice call
- [ ] Verify fallback to SMS when Vapi is unavailable
- [ ] Verify call recording and transcript accessible in dashboard
- [ ] Verify Stripe webhook handles payment success/failure/cancellation
