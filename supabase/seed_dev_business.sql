-- ============================================================
-- CallRecover — Dev Seed: Create a test business
-- ============================================================
-- Run this after all setup scripts to create a test business
-- for local development.
--
-- IMPORTANT: Replace YOUR_SUPABASE_USER_ID below with the
-- actual user ID from Supabase Auth after signing up.
-- You can find it in: Supabase Dashboard → Authentication → Users
-- ============================================================

-- Insert a test HVAC business
INSERT INTO public.businesses (
  id,
  name,
  owner_name,
  owner_email,
  owner_phone,
  business_phone,
  twilio_number,
  timezone,
  business_hours,
  services,
  avg_job_value,
  ai_greeting,
  ai_instructions,
  notification_prefs,
  subscription_status,
  supabase_user_id
) VALUES (
  gen_random_uuid(),
  'Comfort Pro HVAC',
  'Joel Byler',
  'joel@example.com',                     -- Change to your email
  '+15551234567',                          -- Change to your phone
  '+15551234567',                          -- Change to your business phone
  '+15559876543',                          -- Change to your Twilio number
  'America/New_York',
  '{
    "monday":    {"open": "08:00", "close": "17:00"},
    "tuesday":   {"open": "08:00", "close": "17:00"},
    "wednesday": {"open": "08:00", "close": "17:00"},
    "thursday":  {"open": "08:00", "close": "17:00"},
    "friday":    {"open": "08:00", "close": "16:00"},
    "saturday":  {"open": "09:00", "close": "13:00"},
    "sunday":    null
  }'::jsonb,
  ARRAY['AC Repair', 'Heating Repair', 'HVAC Installation', 'Maintenance', 'Duct Cleaning', 'Emergency Service'],
  375.00,
  'Hey! Sorry we missed your call. This is Comfort Pro HVAC. How can we help you today?',
  'We offer 24/7 emergency service for no heat and no AC situations. Always mention our $49 diagnostic special for new customers.',
  '{"sms": true, "email": true, "quiet_start": "21:00", "quiet_end": "07:00"}'::jsonb,
  'active',
  'YOUR_SUPABASE_USER_ID'                 -- ← Replace after signing up
) ON CONFLICT (twilio_number) DO NOTHING;

-- Verify the insert
SELECT id, name, owner_email, supabase_user_id
FROM public.businesses
WHERE name = 'Comfort Pro HVAC';
