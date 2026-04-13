from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.cache import close_redis
from app.routers import hs_codes, chatbot, regulations, history, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


app = FastAPI(
    title="XNK Webapp API",
    description="Tra cứu HS Code & Chatbot AI cho Xuất Nhập Khẩu VN-TQ",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hs_codes.router, prefix="/api/hs-codes", tags=["HS Codes"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["Chatbot"])
app.include_router(regulations.router, prefix="/api/regulations", tags=["Regulations"])
app.include_router(history.router, prefix="/api/history", tags=["History"])
app.include_router(stats.router, prefix="/api/stats", tags=["Stats"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "xnk-webapp-api"}


@app.get("/api/debug-env", tags=["Health"])
async def debug_env():
    """Temporary: verify env vars are loaded."""
    return {
        "SUPABASE_URL": settings.SUPABASE_URL[:30] if settings.SUPABASE_URL else "EMPTY",
        "SUPABASE_KEY_SET": bool(settings.SUPABASE_KEY),
        "GEMINI_MODEL": settings.GEMINI_MODEL.strip(),
        "ENVIRONMENT": settings.ENVIRONMENT.strip(),
    }


@app.get("/api/debug-search", tags=["Health"])
async def debug_search(q: str = "dien thoai"):
    """Temporary: debug Supabase search on Vercel."""
    import traceback
    from app.core.database import get_client
    db = get_client()
    result = {"table_query": None, "rpc_query": None, "error": None}
    try:
        r = db.table("hs_codes").select("code,description_vi").limit(2).execute()
        result["table_query"] = [x["code"] for x in (r.data or [])]
    except Exception as e:
        result["error"] = f"table: {traceback.format_exc()}"
    try:
        r = db.rpc("search_hs_codes", {
            "search_query": q, "result_limit": 3, "sim_threshold": 0.1
        }).execute()
        result["rpc_query"] = [x.get("code") for x in (r.data or [])]
    except Exception as e:
        result["error"] = (result.get("error") or "") + f"\nrpc: {traceback.format_exc()}"
    return result
