from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import hs_codes, chatbot, regulations, history, stats

app = FastAPI(
    title="XNK Webapp API",
    description="Tra cứu HS Code & Chatbot AI cho Xuất Nhập Khẩu VN-TQ",
    version="1.0.0",
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
