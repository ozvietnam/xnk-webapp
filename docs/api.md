# API Reference — XNK Webapp

Interactive docs available at: `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc`

Base URL: `http://localhost:8000`

---

## Health

### `GET /health`

Returns service status. No auth required.

**Response**
```json
{"status": "ok", "service": "xnk-webapp-api"}
```

---

## HS Codes

### `GET /api/hs-codes/search`

Search HS codes using pg_trgm similarity + ILIKE fallback. Results cached 300s in Redis.

**Query parameters**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `q` | string | Yes | — | Search query (tiếng Việt or English) |
| `limit` | int | No | 20 | Max results (1–100) |
| `threshold` | float | No | 0.15 | pg_trgm similarity threshold (0.0–1.0) |

**Example**
```bash
curl "http://localhost:8000/api/hs-codes/search?q=điện+thoại&limit=5"
```

**Response**
```json
{
  "results": [
    {
      "id": "uuid",
      "code": "8517.12.00",
      "description_vi": "Điện thoại thông minh",
      "description_en": "Smartphones",
      "unit": "chiếc",
      "tax_rate_normal": 10.0,
      "tax_rate_preferential": 0.0,
      "tax_rate_special": null,
      "notes": null,
      "similarity_score": 0.379
    }
  ],
  "total": 1,
  "query": "điện thoại"
}
```

**Notes**
- `similarity_score` is null for ILIKE fallback results
- Lower `threshold` = more results but less precise
- Search by HS code prefix also works: `?q=8517`

---

### `GET /api/hs-codes/{code}`

Get full details of a single HS code. Cached 3600s in Redis.

**Path parameters**

| Param | Type | Description |
|-------|------|-------------|
| `code` | string | HS code (e.g. `8517.12.00`) |

**Example**
```bash
curl "http://localhost:8000/api/hs-codes/8517.12.00"
```

**Response**
```json
{
  "id": "uuid",
  "code": "8517.12.00",
  "description_vi": "Điện thoại thông minh",
  "description_en": "Smartphones",
  "unit": "chiếc",
  "tax_rate_normal": 10.0,
  "tax_rate_preferential": 0.0,
  "tax_rate_special": null,
  "notes": "ACFTA rate applicable for imports from China"
}
```

**Error**
```json
// 404
{"detail": "HS code 9999.99.99 not found"}
```

---

## Chatbot

### `POST /api/chatbot/ask`

RAG chatbot: searches HS DB → builds context → calls Ollama qwen2.5-coder:32b.

**Rate limit**: 20 requests per IP per 60 seconds. Returns `429` if exceeded.

**Headers**

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | No | `Bearer <supabase-jwt>` — enables history logging |

**Request body**
```json
{
  "question": "Điện thoại di động nhập từ Trung Quốc chịu thuế bao nhiêu?",
  "session_id": "optional-session-uuid"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes | User question in Vietnamese or English |
| `session_id` | string | No | UUID for session grouping in history |

**Example**
```bash
curl -X POST http://localhost:8000/api/chatbot/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Thuế nhập khẩu laptop từ Trung Quốc?"}'
```

**Response**
```json
{
  "answer": "Laptop (HS 8471.30.00) nhập từ Trung Quốc theo ACFTA: 0%. Thuế MFN: 0%. Miễn thuế hoàn toàn.",
  "citations": ["8471.30.00", "8517.12.00"],
  "session_id": "optional-session-uuid"
}
```

**Error (429)**
```json
{
  "detail": "Quá nhiều yêu cầu. Giới hạn 20 lần/60s mỗi IP.",
  "Retry-After": "60"
}
```

---

## Regulations

### `GET /api/regulations`

List customs regulations. Supports category filter.

**Query parameters**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `category` | string | No | all | `thu-tuc`, `chung-tu`, `thue`, `kiem-tra` |
| `limit` | int | No | 50 | Max results |

**Example**
```bash
curl "http://localhost:8000/api/regulations?category=thue&limit=10"
```

**Response**
```json
{
  "results": [
    {
      "id": "uuid",
      "category": "thue",
      "title": "Biểu thuế MFN 2024",
      "content_vi": "...",
      "effective_date": "2024-01-01",
      "source_document": "Nghị định XX/2024/NĐ-CP",
      "tags": ["thuế", "MFN"],
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

---

### `GET /api/regulations/{id}`

Get a single regulation by UUID.

**Example**
```bash
curl "http://localhost:8000/api/regulations/550e8400-e29b-41d4-a716-446655440000"
```

---

## History

### `GET /api/history`

Get search history for the authenticated user. Requires auth.

**Headers**: `Authorization: Bearer <supabase-jwt>`

**Query parameters**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 50 | Max results |

**Response**
```json
{
  "results": [
    {
      "id": "uuid",
      "query": "điện thoại",
      "result_codes": ["8517.12.00"],
      "created_at": "2024-01-01T10:00:00Z"
    }
  ],
  "total": 1
}
```

**Error (401)**: `{"detail": "Authentication required"}`

---

## Stats

### `GET /api/stats`

Public statistics — totals and popular queries.

**Example**
```bash
curl "http://localhost:8000/api/stats"
```

**Response**
```json
{
  "total_hs_codes": 50,
  "total_searches": 1234,
  "total_regulations": 0,
  "popular_queries": [
    {"query": "điện thoại", "count": 42},
    {"query": "laptop", "count": 31}
  ]
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad request / validation error |
| 401 | Missing or invalid auth token |
| 404 | Resource not found |
| 422 | Unprocessable entity (missing required field) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

## OpenAPI Export

Export the full OpenAPI JSON spec:

```bash
cd backend
source venv/bin/activate
python scripts/export_openapi.py > docs/openapi.json
```
