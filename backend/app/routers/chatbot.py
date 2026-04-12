from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client
from app.core.deps import get_db, get_current_user_id
from app.core.rate_limit import rate_limit
from app.models.schemas import ChatRequest, ChatResponse
from app.services import chatbot as chatbot_service

router = APIRouter()

CHATBOT_RATE_LIMIT = 20   # requests
CHATBOT_RATE_WINDOW = 60  # seconds


@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(
    request: Request,
    body: ChatRequest,
    db: Client = Depends(get_db),
    user_id: str | None = Depends(get_current_user_id),
):
    await rate_limit(request, limit=CHATBOT_RATE_LIMIT, window=CHATBOT_RATE_WINDOW)
    return await chatbot_service.ask(db, body, user_id)
