from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.core.deps import get_db, get_current_user_id
from app.models.schemas import ChatRequest, ChatResponse
from app.services import chatbot as chatbot_service

router = APIRouter()


@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(
    request: ChatRequest,
    db: Client = Depends(get_db),
    user_id: str | None = Depends(get_current_user_id),
):
    return await chatbot_service.ask(db, request, user_id)
