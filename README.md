# XNK Webapp — Tra cứu HS Code & Chatbot AI

Ứng dụng tra cứu mã HS Code và tư vấn xuất nhập khẩu Việt Nam – Trung Quốc, tích hợp AI chatbot qua Ollama (qwen2.5-coder:32b).

## Tính năng

- **Tra cứu HS Code**: Tìm kiếm mã HS bằng tiếng Việt/Anh, xem thuế suất MFN và ACFTA
- **Chatbot AI**: Tư vấn phân loại hàng hóa, thuế suất, thủ tục hải quan qua RAG + Ollama
- **Quy định**: Danh sách thủ tục, chứng từ, thuế, kiểm tra chuyên ngành
- **Dashboard**: Lịch sử tra cứu và thống kê cá nhân (cần đăng nhập)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 + FastAPI |
| Database | Supabase PostgreSQL + pg_trgm |
| Frontend | Next.js 14 App Router + TypeScript + Tailwind CSS |
| AI | Ollama local (qwen2.5-coder:32b) |
| Auth | Supabase Auth |
| Cache | Redis (optional, fallback to memory) |
| Deploy | Docker Compose |

## Yêu cầu

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose (cho production)
- Ollama ([ollama.ai](https://ollama.ai)) với model `qwen2.5-coder:32b`
- Supabase project (free tier đủ dùng)

## Cài đặt nhanh

### 1. Clone & setup env

```bash
git clone <repo-url>
cd xnk-webapp
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

### 2. Cấu hình `.env`

```bash
# backend/.env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:32b
```

```bash
# frontend/.env.local
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Khởi động Ollama

```bash
ollama serve
ollama pull qwen2.5-coder:32b
```

### 4. Chạy migration & seed

```bash
cd backend
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python scripts/run_migration.py
python scripts/seed_hs_codes.py
```

### 5. Chạy backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 6. Chạy frontend

```bash
cd frontend
npm install
npm run dev
```

Truy cập: http://localhost:3000

## Docker Compose (Production)

```bash
# Tạo .env files trước (xem bước 2 ở trên)
docker compose up --build -d
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Redis: localhost:6379

> **Lưu ý**: Ollama cần chạy riêng trên host machine và `OLLAMA_BASE_URL=http://host.docker.internal:11434` trong backend/.env khi chạy Docker.

## API Endpoints

Xem đầy đủ tại http://localhost:8000/docs (Swagger UI) hoặc http://localhost:8000/redoc

| Method | Path | Auth | Mô tả |
|--------|------|------|-------|
| GET | /health | No | Health check |
| GET | /api/hs-codes/search?q=&limit= | No | Tìm kiếm HS code (pg_trgm) |
| GET | /api/hs-codes/{code} | No | Chi tiết mã HS |
| POST | /api/chatbot/ask | Optional | Chatbot AI (RAG + Ollama) |
| GET | /api/regulations?category= | No | Danh sách quy định |
| GET | /api/regulations/{id} | No | Chi tiết quy định |
| GET | /api/history | Yes | Lịch sử tra cứu của user |
| GET | /api/stats | No | Thống kê tổng quan |

### Chatbot request/response

```json
// POST /api/chatbot/ask
{
  "question": "Điện thoại di động nhập từ Trung Quốc chịu thuế bao nhiêu?",
  "session_id": "optional-session-id"
}

// Response
{
  "answer": "Điện thoại di động (HS 8517.12.00) nhập từ Trung Quốc theo ACFTA: 0%. Thuế MFN: 10%.",
  "citations": ["8517.12.00"],
  "session_id": "optional-session-id"
}
```

## Cấu trúc project

```
xnk-webapp/
├── backend/
│   ├── app/
│   │   ├── core/        # config, database, cache, rate_limit, deps
│   │   ├── models/      # Pydantic schemas
│   │   ├── routers/     # FastAPI routes
│   │   └── services/    # Business logic (hs_search, chatbot, history…)
│   ├── scripts/         # Migration, seed scripts
│   ├── tests/           # pytest unit + integration tests
│   └── requirements.txt
├── frontend/
│   ├── app/             # Next.js 14 App Router pages
│   ├── components/      # Navbar, Footer, UI components
│   └── lib/             # API client, Supabase client
├── supabase/
│   └── migrations/      # SQL migration files
├── docker-compose.yml
└── architecture.md
```

## Tests

```bash
cd backend
venv/bin/python -m pytest tests/ -v
```

17 unit tests (no external calls) — cache, rate_limit, chatbot, health.

## Dữ liệu

- 50 mã HS codes phổ biến thương mại VN-TQ (seed tự động)
- Categories: điện tử, máy móc, thép/nhôm, nhựa/cao su, dệt may/giày dép, gỗ/nội thất, hóa chất, xe cộ, y tế, nông sản
- Tìm kiếm bằng pg_trgm: hỗ trợ tiếng Việt, từ khóa tiếng Anh, prefix mã HS
