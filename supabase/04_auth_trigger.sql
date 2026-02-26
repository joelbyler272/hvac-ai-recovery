-- ============================================================
-- CallHook — Supabase Setup: Step 4 — Auth Trigger
-- ============================================================
-- This trigger automatically creates a Business record when
-- a new user signs up via Supabase Auth. The business starts
-- with placeholder data that the owner fills in on first login.
--
-- The supabase_user_id column links the auth.users record
-- to the business, enabling multi-tenant data access.
-- ============================================================

-- Function: runs after a new user is created in auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.businesses (
    id,
    name,
    owner_name,
    owner_email,
    owner_phone,
    business_phone,
    twilio_number,
    supabase_user_id,
    subscription_status
  ) VALUES (
    gen_random_uuid(),
    COALESCE(NEW.raw_user_meta_data->>'business_name', 'My Business'),
    COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'phone', ''),
    COALESCE(NEW.raw_user_meta_data->>'phone', ''),
    'pending-setup',  -- Placeholder until Twilio number is assigned
    NEW.id::text,
    'trial'
  );
  RETURN NEW;
END;
$$;

-- Drop existing trigger if re-running
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Create trigger on auth.users
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();
