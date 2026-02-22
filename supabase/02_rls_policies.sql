-- ============================================================
-- CallRecover — Supabase Setup: Step 2 — Row Level Security
-- ============================================================
-- Run this AFTER the Alembic migration has created all tables.
--
-- These policies ensure each business can only access their
-- own data via the Supabase client (frontend realtime, etc.).
-- The backend uses the service_role key which bypasses RLS.
-- ============================================================

-- ── Helper function: get business_id for current JWT user ──
CREATE OR REPLACE FUNCTION public.get_current_business_id()
RETURNS UUID
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
  SELECT id FROM public.businesses
  WHERE supabase_user_id = auth.uid()::text
  LIMIT 1;
$$;

-- ============================================================
-- Enable RLS on all tables
-- ============================================================
ALTER TABLE public.businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.review_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.opt_outs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_metrics ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Businesses — owner can read/update their own record
-- ============================================================
CREATE POLICY "businesses_select_own"
  ON public.businesses FOR SELECT
  USING (supabase_user_id = auth.uid()::text);

CREATE POLICY "businesses_update_own"
  ON public.businesses FOR UPDATE
  USING (supabase_user_id = auth.uid()::text)
  WITH CHECK (supabase_user_id = auth.uid()::text);

-- ============================================================
-- Calls — scoped to business
-- ============================================================
CREATE POLICY "calls_select_own"
  ON public.calls FOR SELECT
  USING (business_id = public.get_current_business_id());

CREATE POLICY "calls_insert_own"
  ON public.calls FOR INSERT
  WITH CHECK (business_id = public.get_current_business_id());

-- ============================================================
-- Leads — scoped to business
-- ============================================================
CREATE POLICY "leads_select_own"
  ON public.leads FOR SELECT
  USING (business_id = public.get_current_business_id());

CREATE POLICY "leads_insert_own"
  ON public.leads FOR INSERT
  WITH CHECK (business_id = public.get_current_business_id());

CREATE POLICY "leads_update_own"
  ON public.leads FOR UPDATE
  USING (business_id = public.get_current_business_id());

-- ============================================================
-- Conversations — scoped to business
-- ============================================================
CREATE POLICY "conversations_select_own"
  ON public.conversations FOR SELECT
  USING (business_id = public.get_current_business_id());

CREATE POLICY "conversations_insert_own"
  ON public.conversations FOR INSERT
  WITH CHECK (business_id = public.get_current_business_id());

CREATE POLICY "conversations_update_own"
  ON public.conversations FOR UPDATE
  USING (business_id = public.get_current_business_id());

-- ============================================================
-- Messages — scoped to business
-- ============================================================
CREATE POLICY "messages_select_own"
  ON public.messages FOR SELECT
  USING (business_id = public.get_current_business_id());

CREATE POLICY "messages_insert_own"
  ON public.messages FOR INSERT
  WITH CHECK (business_id = public.get_current_business_id());

-- ============================================================
-- Appointments — scoped to business
-- ============================================================
CREATE POLICY "appointments_select_own"
  ON public.appointments FOR SELECT
  USING (business_id = public.get_current_business_id());

CREATE POLICY "appointments_insert_own"
  ON public.appointments FOR INSERT
  WITH CHECK (business_id = public.get_current_business_id());

CREATE POLICY "appointments_update_own"
  ON public.appointments FOR UPDATE
  USING (business_id = public.get_current_business_id());

-- ============================================================
-- Review Requests — scoped to business
-- ============================================================
CREATE POLICY "review_requests_select_own"
  ON public.review_requests FOR SELECT
  USING (business_id = public.get_current_business_id());

-- ============================================================
-- Opt-Outs — scoped to business (nullable business_id)
-- ============================================================
CREATE POLICY "opt_outs_select_own"
  ON public.opt_outs FOR SELECT
  USING (business_id = public.get_current_business_id() OR business_id IS NULL);

-- ============================================================
-- Audit Log — scoped to business
-- ============================================================
CREATE POLICY "audit_log_select_own"
  ON public.audit_log FOR SELECT
  USING (business_id = public.get_current_business_id());

-- ============================================================
-- Daily Metrics — scoped to business
-- ============================================================
CREATE POLICY "daily_metrics_select_own"
  ON public.daily_metrics FOR SELECT
  USING (business_id = public.get_current_business_id());
