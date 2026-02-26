-- ============================================================
-- CallHook — Supabase Setup: Step 5 — Auto-update timestamps
-- ============================================================
-- Automatically set updated_at on row changes.
-- The backend ORM handles this too, but this ensures it works
-- for any direct SQL updates or Supabase client writes.
-- ============================================================

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

-- Businesses
DROP TRIGGER IF EXISTS set_businesses_updated_at ON public.businesses;
CREATE TRIGGER set_businesses_updated_at
  BEFORE UPDATE ON public.businesses
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Leads
DROP TRIGGER IF EXISTS set_leads_updated_at ON public.leads;
CREATE TRIGGER set_leads_updated_at
  BEFORE UPDATE ON public.leads
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Conversations
DROP TRIGGER IF EXISTS set_conversations_updated_at ON public.conversations;
CREATE TRIGGER set_conversations_updated_at
  BEFORE UPDATE ON public.conversations
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Appointments
DROP TRIGGER IF EXISTS set_appointments_updated_at ON public.appointments;
CREATE TRIGGER set_appointments_updated_at
  BEFORE UPDATE ON public.appointments
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
