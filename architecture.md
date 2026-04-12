# XNK Webapp — System Architecture

## Overview

```
[Browser]
    │
    ▼
[Next.js :3000]  ──── Supabase Auth ────►  [Supabase Auth]
    │
    │ HTTP / REST
    ▼
[FastAPI :8000]
    ├──► [Supabase PostgreSQL]  (hs_codes, regulations, history)
    └──► [Claude API]           (claude-sonnet-4-20250514)
```

## Component Responsibilities

| Component | Port | Responsibility |
|-----------|------|---------------|
| Next.js | 3000 | UI, SSR, auth middleware, API calls |
| FastAPI | 8000 | Business logic, DB queries, Claude integration |
| Supabase | cloud | PostgreSQL + Auth + RLS |
| Claude API | cloud | AI chatbot responses |

## Data Flow — HS Code Search

```
User types query
    │
    ▼
Next.js /tra-cuu-hs
    │ GET /api/hs-codes/search?q={query}
    ▼
FastAPI hs_codes router
    │
    ▼
hs_search service
    │ pg_trgm similarity_threshold = 0.3
    │ ORDER BY similarity DESC, code ASC
    │ LIMIT 20
    ▼
Supabase PostgreSQL
    │ GIN index on description_vi
    ▼
Return [{code, description_vi, tax_rate_normal, ...}]
    │
    ▼
Next.js renders results table
```

## Data Flow — Chatbot

```
User question
    │
    ▼
POST /api/chatbot/ask {question, session_id}
    │
    ▼ Step 1: RAG
Search HS DB (top 5 relevant codes)
Search regulations (if applicable)
    │
    ▼ Step 2: Build prompt
System: "Bạn là chuyên gia XNK Việt Nam..."
Context: [top 5 HS codes + regulations]
User: question
    │
    ▼ Step 3: Claude API
claude-sonnet-4-20250514
max_tokens: 1024
    │
    ▼ Step 4: Log & Return
Save to search_history
Return {answer, citations: [HS codes used], session_id}
```

## Security

- RLS on search_history: users see only their own records
- service_role key: only used backend-side, never exposed to frontend
- anon key: frontend-safe, limited permissions
- /chatbot and /dashboard: protected by Next.js middleware + Supabase session check

## Performance Strategy

- pg_trgm GIN index: fast similarity search on Vietnamese text
- Redis cache (T14): cache search results 5 minutes
- Rate limit (T14): chatbot max 20 req/min/user
- Static generation for landing + quy-dinh pages where possible
