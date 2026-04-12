# Environment Variables Setup

## Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | Yes | — | Supabase project URL (https://xxx.supabase.co) |
| `SUPABASE_KEY` | Yes | — | Supabase anon/public key |
| `SUPABASE_SERVICE_KEY` | Yes | — | Supabase service_role key (bypasses RLS) |
| `DATABASE_URL` | Yes (migrations) | — | PostgreSQL connection string for psycopg2 |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama server base URL |
| `OLLAMA_MODEL` | No | `qwen2.5-coder:32b` | Ollama model name |
| `REDIS_URL` | No | `redis://localhost:6379` | Redis connection URL |
| `PORT` | No | `8000` | Backend server port |
| `ENVIRONMENT` | No | `development` | `development` or `production` |

### Where to find Supabase credentials

1. Go to your Supabase project → **Settings** → **API**
2. Copy **Project URL** → `SUPABASE_URL`
3. Copy **anon public** key → `SUPABASE_KEY`
4. Copy **service_role** key → `SUPABASE_SERVICE_KEY`
5. Go to **Settings** → **Database** → Connection string (URI mode) → `DATABASE_URL`

### Docker production override

When backend runs inside Docker, Ollama is on the host machine:
```
OLLAMA_BASE_URL=http://host.docker.internal:11434
REDIS_URL=redis://redis:6379
```

---

## Frontend (`frontend/.env.local`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | — | Same as backend `SUPABASE_URL` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | — | Same as backend `SUPABASE_KEY` |
| `NEXT_PUBLIC_API_URL` | Yes | `http://localhost:8000` | Backend API base URL |

### Docker production override

```
NEXT_PUBLIC_API_URL=http://backend:8000
```
(Docker Compose handles internal DNS, so `backend` resolves to the backend service.)

For public-facing deployments, set this to your public domain:
```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

## Security Notes

- Never commit `.env` or `.env.local` to git (both are in `.gitignore`)
- `SUPABASE_SERVICE_KEY` bypasses RLS — keep it backend-only, never expose to frontend
- `NEXT_PUBLIC_*` variables are embedded in the browser bundle — never put secrets there
- The anon key (`SUPABASE_KEY`) is safe to expose; RLS policies control data access

---

## Example `.env.example`

```bash
# backend/.env.example
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGci...
SUPABASE_SERVICE_KEY=eyJhbGci...
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:32b
REDIS_URL=redis://localhost:6379
PORT=8000
ENVIRONMENT=development
```

```bash
# frontend/.env.local.example
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...
NEXT_PUBLIC_API_URL=http://localhost:8000
```
