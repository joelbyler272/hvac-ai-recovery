-- ============================================================
-- CallHook — Supabase Setup: Step 3 — Realtime
-- ============================================================
-- Enable Supabase Realtime (postgres_changes) on the tables
-- the frontend subscribes to. This allows the dashboard to
-- update in real-time when new calls, messages, or leads
-- arrive.
--
-- NOTE: You can also enable these via the Supabase Dashboard:
--   Database → Replication → Manage publications
--   Toggle the tables listed below.
-- ============================================================

-- Create a dedicated publication for realtime
-- (Supabase uses "supabase_realtime" by default)
DO $$
DECLARE
  _tbl text;
BEGIN
  -- Remove existing entries to avoid errors on re-run
  FOREACH _tbl IN ARRAY ARRAY['calls','messages','leads','conversations']
  LOOP
    BEGIN
      EXECUTE format('ALTER PUBLICATION supabase_realtime DROP TABLE public.%I', _tbl);
    EXCEPTION WHEN undefined_object THEN
      -- table wasn't in the publication, ignore
    END;
  END LOOP;
END
$$;

-- Add tables the frontend subscribes to
ALTER PUBLICATION supabase_realtime ADD TABLE public.calls;
ALTER PUBLICATION supabase_realtime ADD TABLE public.messages;
ALTER PUBLICATION supabase_realtime ADD TABLE public.leads;
ALTER PUBLICATION supabase_realtime ADD TABLE public.conversations;
