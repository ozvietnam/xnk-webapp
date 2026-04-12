# CLAUDE.md — XNK Webapp Mandatory Workflow

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 + FastAPI + SQLAlchemy |
| Database | Supabase PostgreSQL + pg_trgm |
| Frontend | Next.js 14 App Router + TypeScript strict + Tailwind CSS |
| AI | Claude API (`claude-sonnet-4-20250514`) |
| Auth | Supabase Auth |
| Tests | pytest (backend) + Playwright (E2E) |
| Deploy | Docker Compose |

---

## 6-Step Workflow — BẮT BUỘC mỗi session

```
Step 1 → ./init.sh              Khởi động môi trường
Step 2 → Đọc task.json         Chọn task đầu tiên passes=false, dependencies done
Step 3 → Implement             FastAPI router → service → repository → Supabase
Step 4 → Test                  pytest + lint + build + Playwright screenshot
Step 5 → progress.txt          Ghi kết quả
Step 6 → Git commit            git commit -m "[Txx] description - completed"
```

---

## Blocking Rules — DỪNG khi gặp

- Thiếu env vars bắt buộc → ghi `BLOCKED: missing env` vào progress.txt
- External API fail (Supabase, Claude) → ghi `BLOCKED: API error` → báo user
- pytest fail 3 lần liên tiếp → ghi `BLOCKED: test fail` → báo user
- Thiếu seed data (T03 chưa done khi cần) → ghi `BLOCKED: no seed data`

---

## Implementation Pattern

### Backend (FastAPI)

```
backend/
├── main.py              FastAPI app entry
├── routers/
│   ├── hs_codes.py      GET /api/hs-codes/search, GET /api/hs-codes/{code}
│   ├── chatbot.py       POST /api/chatbot/ask
│   ├── regulations.py   GET /api/regulations
│   ├── history.py       GET /api/history
│   └── stats.py         GET /api/stats
├── services/
│   ├── hs_search.py     pg_trgm similarity search logic
│   ├── chatbot.py       Claude API + RAG logic
│   └── regulations.py
├── repositories/
│   ├── hs_codes.py      DB queries (SQLAlchemy / supabase-py)
│   └── regulations.py
├── models/
│   └── schemas.py       Pydantic models
├── core/
│   ├── config.py        Settings (pydantic-settings)
│   ├── database.py      Supabase client
│   └── deps.py          FastAPI dependencies
├── requirements.txt
└── .env.example
```

### Frontend (Next.js 14)

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx             / (landing)
│   ├── tra-cuu-hs/
│   │   └── page.tsx
│   ├── chatbot/
│   │   └── page.tsx         (protected)
│   ├── quy-dinh/
│   │   └── page.tsx
│   ├── dashboard/
│   │   └── page.tsx         (protected)
│   └── dang-nhap/
│       └── page.tsx
├── components/
│   ├── Navbar.tsx
│   ├── Footer.tsx
│   └── ui/                  Reusable components
├── lib/
│   ├── api.ts               API client
│   └── supabase.ts          Supabase client
├── types/
│   └── index.ts
├── middleware.ts             Auth protection
├── tailwind.config.ts
├── tsconfig.json
└── .env.local.example
```

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /health | No | Health check |
| GET | /api/hs-codes/search?q=&limit= | No | pg_trgm search |
| GET | /api/hs-codes/{code} | No | Chi tiết mã HS |
| POST | /api/chatbot/ask | Yes | Chatbot AI |
| GET | /api/regulations | No | Danh sách quy định |
| GET | /api/history | Yes | Search history của user |
| GET | /api/stats | No | Thống kê tổng quan |

---

## Database Schema

```sql
-- hs_codes
CREATE TABLE hs_codes (
  id BIGSERIAL PRIMARY KEY,
  code VARCHAR(10) UNIQUE NOT NULL,
  description_vi TEXT NOT NULL,
  description_en TEXT,
  unit VARCHAR(50),
  tax_rate_normal DECIMAL(5,2),
  tax_rate_preferential DECIMAL(5,2),  -- ACFTA/RCEP
  tax_rate_special DECIMAL(5,2),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- hs_chapters
CREATE TABLE hs_chapters (
  chapter_code VARCHAR(2) PRIMARY KEY,
  title_vi TEXT NOT NULL,
  title_en TEXT
);

-- customs_regulations
CREATE TABLE customs_regulations (
  id BIGSERIAL PRIMARY KEY,
  category VARCHAR(50),
  title TEXT NOT NULL,
  content_vi TEXT,
  effective_date DATE,
  source_document VARCHAR(200),
  tags JSONB DEFAULT '[]'
);

-- search_history
CREATE TABLE search_history (
  id BIGSERIAL PRIMARY KEY,
  query TEXT NOT NULL,
  result_codes JSONB DEFAULT '[]',
  user_id UUID REFERENCES auth.users(id),
  user_session VARCHAR(100),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- user_profiles
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT,
  company_name TEXT,
  role VARCHAR(50) DEFAULT 'user'
);
```

---

## Env Variables

### Backend `.env`
```
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=
CLAUDE_API_KEY=
PORT=8000
ENVIRONMENT=development
```

### Frontend `.env.local`
```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Chatbot Flow

```
User message
    │
    ▼
Search HS DB (pg_trgm, top 5 results)
    │
    ▼
Build context: question + HS results + regulations
    │
    ▼
Call Claude API (claude-sonnet-4-20250514)
    │
    ▼
Return answer + citations
    │
    ▼
Log to search_history
```

---

## Commit Format

```
git commit -m "[T01] Project scaffold - completed"
git commit -m "[T02] Supabase schema migration - completed"
git commit -m "[T03] Seed 50 HS codes - completed"
```
