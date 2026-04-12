# Deployment Guide — XNK Webapp

## Prerequisites

| Tool | Version |
|------|---------|
| Docker | 24+ |
| Docker Compose | 2.20+ |
| Ollama | latest |
| Supabase project | free tier |

---

## Local Development

### 1. Environment files

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

Edit `backend/.env`:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:32b
REDIS_URL=redis://localhost:6379
```

Edit `frontend/.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Start Ollama

```bash
ollama serve
ollama pull qwen2.5-coder:32b   # ~20GB download on first run
```

### 3. Database setup

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python scripts/run_migration.py    # creates tables, indexes, functions
python scripts/seed_hs_codes.py   # seeds 50 HS codes
```

### 4. Start Redis (optional, improves performance)

```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine \
  redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### 5. Start backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 6. Start frontend

```bash
cd frontend
npm install
npm run dev
```

App available at: http://localhost:3000
API docs at: http://localhost:8000/docs

---

## Docker Compose (Production)

### Service topology

```
                 ┌─────────┐
                 │  nginx  │  (optional reverse proxy)
                 └────┬────┘
           ┌──────────┴──────────┐
      ┌────▼────┐          ┌─────▼────┐
      │frontend │          │ backend  │
      │ :3000   │          │  :8000   │
      └─────────┘          └────┬─────┘
                                │
                     ┌──────────┴──────────┐
               ┌─────▼────┐        ┌───────▼──────┐
               │  Redis   │        │  Supabase    │
               │  :6379   │        │  (external)  │
               └──────────┘        └──────────────┘
                                          │
                                   ┌──────▼──────┐
                                   │   Ollama    │
                                   │ (host:11434)│
                                   └─────────────┘
```

### Steps

```bash
# 1. Ensure Ollama is running on host
ollama serve &
ollama pull qwen2.5-coder:32b

# 2. Set OLLAMA_BASE_URL in backend/.env for Docker:
#    OLLAMA_BASE_URL=http://host.docker.internal:11434

# 3. Build and start all services
docker compose up --build -d

# 4. Run migrations (first time only)
docker compose exec backend python scripts/run_migration.py
docker compose exec backend python scripts/seed_hs_codes.py

# 5. Check health
curl http://localhost:8000/health
```

### Service URLs (production)

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Redis | localhost:6379 (internal only) |

### Logs

```bash
docker compose logs -f backend     # backend logs
docker compose logs -f frontend    # frontend logs
docker compose logs -f redis       # Redis logs
```

### Restart a service

```bash
docker compose restart backend
```

### Update deployment

```bash
git pull
docker compose up --build -d
```

---

## Environment Variables Reference

See [env-setup.md](./env-setup.md) for complete variable documentation.

---

## Health Checks

| Endpoint | Expected |
|----------|---------|
| `GET /health` | `{"status": "ok"}` |
| `GET /api/stats` | JSON with counts |
| Redis | `redis-cli ping` → `PONG` |

---

## Performance Notes

- Redis cache TTL: 300s for search, 3600s for detail pages
- Rate limit: 20 chatbot requests per IP per 60 seconds
- Ollama response time: 15-60s depending on query complexity and hardware
- pg_trgm threshold default: 0.15 (tune via `?threshold=` param)
