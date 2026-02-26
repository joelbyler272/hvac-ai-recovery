-- ============================================================
-- CallHook — Supabase Setup: Step 1 — Extensions
-- ============================================================
-- Run this FIRST in the Supabase SQL Editor.
-- These extensions are needed before creating tables.
-- ============================================================

-- UUID generation (gen_random_uuid)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Already enabled by default in Supabase, but be explicit:
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
