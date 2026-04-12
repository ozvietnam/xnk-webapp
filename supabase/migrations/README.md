# Supabase Migrations

Migrations are applied in order. Run via Supabase CLI or the Supabase dashboard.

## T02 (pending Supabase credentials):
- `001_create_extensions.sql` — pg_trgm, uuid-ossp
- `002_create_hs_chapters.sql`
- `003_create_hs_codes.sql` + GIN index
- `004_create_regulations.sql`
- `005_create_search_history.sql`
- `006_create_user_profiles.sql`
- `007_rls_policies.sql`
