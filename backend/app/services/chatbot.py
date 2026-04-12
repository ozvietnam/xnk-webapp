from supabase import Client
from app.models.schemas import ChatRequest, ChatResponse
from app.core.config import settings


async def ask(db: Client, request: ChatRequest, user_id: str | None) -> ChatResponse:
    """
    Chatbot flow:
    1. Search HS DB (top 5 relevant codes)
    2. Build context prompt
    3. Call Claude API (claude-sonnet-4-20250514)
    4. Log to search_history
    5. Return answer + citations
    """
    # T05 will implement. Requires CLAUDE_API_KEY + T04 search.
    raise NotImplementedError("Requires T04 (HS search) + CLAUDE_API_KEY")
