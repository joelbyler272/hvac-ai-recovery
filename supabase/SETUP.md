# Supabase Setup Guide

Complete guide to set up Supabase for CallRecover.

## 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Choose a region close to your users (e.g., `us-east-1`)
3. Set a strong database password — save it somewhere safe
4. Wait for the project to finish provisioning (~2 minutes)

## 2. Get Your Credentials

Go to **Settings → API** and copy:

| Variable | Where to find it |
|----------|-----------------|
| `SUPABASE_URL` | Project URL |
| `SUPABASE_ANON_KEY` | `anon` / `public` key |
| `SUPABASE_SERVICE_ROLE_KEY` | `service_role` key (keep secret!) |

Go to **Settings → Database → Connection string** and copy:
- Select **URI** format
- Replace `[YOUR-PASSWORD]` with the database password you set

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres` |

Add these to your `.env` file.

Also set the frontend variables:
```
NEXT_PUBLIC_SUPABASE_URL=<same as SUPABASE_URL>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<same as SUPABASE_ANON_KEY>
```

## 3. Run the Alembic Migration

This creates all 10 database tables:

```bash
cd backend
alembic upgrade head
```

You should see output like:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema
```

## 4. Run the Supabase SQL Scripts

Open the **SQL Editor** in your Supabase Dashboard and run each script **in order**:

1. **`01_enable_extensions.sql`** — Enables pgcrypto for UUID generation
2. **`02_rls_policies.sql`** — Sets up Row Level Security so each business can only see their own data
3. **`03_realtime.sql`** — Enables real-time subscriptions on calls, messages, leads, conversations
4. **`04_auth_trigger.sql`** — Auto-creates a business record when a user signs up
5. **`05_updated_at_trigger.sql`** — Auto-updates `updated_at` timestamps

> **Tip:** You can paste and run each file directly in the Supabase SQL Editor, or combine them all into one run.

## 5. Configure Auth

### Enable Email/Password Auth

1. Go to **Authentication → Providers**
2. Enable **Email** provider
3. Optionally disable "Confirm email" for local dev (under **Authentication → Settings → Email Auth**)

### Set Redirect URLs

1. Go to **Authentication → URL Configuration**
2. Set **Site URL** to: `http://localhost:3000` (for dev)
3. Add **Redirect URLs**:
   - `http://localhost:3000/**`
   - `https://your-production-domain.com/**` (for production)

## 6. Verify Realtime is Enabled

1. Go to **Database → Replication**
2. Click on the `supabase_realtime` publication
3. Verify these tables are listed:
   - `calls`
   - `messages`
   - `leads`
   - `conversations`

If they're missing, the `03_realtime.sql` script may not have run. Run it again.

## 7. Create Your First User

### Option A: Sign up through the app
1. Start the frontend: `cd frontend && npm run dev`
2. Go to `http://localhost:3000` and sign up with email/password
3. The auth trigger will automatically create a business record
4. Update the business details via the Settings page

### Option B: Use the seed script
1. Sign up through the Supabase Dashboard: **Authentication → Users → Add User**
2. Copy the user's UUID
3. Edit `seed_dev_business.sql` — replace `YOUR_SUPABASE_USER_ID` with the UUID
4. Run the script in the SQL Editor

## 8. Verify Everything Works

Run a quick check in the SQL Editor:

```sql
-- Should show your tables
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Should show your business
SELECT id, name, supabase_user_id FROM businesses;

-- Should show RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';

-- Should show realtime publications
SELECT * FROM pg_publication_tables
WHERE pubname = 'supabase_realtime';
```

## Troubleshooting

### "permission denied for table businesses"
RLS is enabled but no policy matches. Make sure:
- You're authenticated (JWT token in the request)
- The `supabase_user_id` on your business record matches your auth user ID

### Realtime not working
- Check that the tables are in the `supabase_realtime` publication (step 6)
- Check browser console for WebSocket connection errors
- Make sure `NEXT_PUBLIC_SUPABASE_URL` is set in the frontend

### Auth trigger not creating business
- Check the trigger exists: `SELECT * FROM information_schema.triggers WHERE trigger_name = 'on_auth_user_created';`
- Check for errors in the Supabase logs: **Logs → Postgres**

### Database connection refused
- Make sure your `DATABASE_URL` uses the correct password
- For Supabase, the connection string format is:
  `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
- If using connection pooling, use port `6543` instead of `5432`
