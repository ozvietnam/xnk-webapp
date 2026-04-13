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
    """Temporary: verify env vars are loaded (shows only first 20 chars)."""
    return {
        "SUPABASE_URL": settings.SUPABASE_URL[:30] if settings.SUPABASE_URL else "EMPTY",
        "SUPABASE_KEY": settings.SUPABASE_KEY[:20] + "..." if settings.SUPABASE_KEY else "EMPTY",
        "GEMINI_MODEL": settings.GEMINI_MODEL,
        "ENVIRONMENT": settings.ENVIRONMENT,
    }
