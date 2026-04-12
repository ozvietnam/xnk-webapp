from supabase import Client
from app.models.schemas import SearchHistoryItem
from typing import List


async def get_user_history(db: Client, user_id: str) -> List[SearchHistoryItem]:
    raise NotImplementedError("Requires T11 Auth + T12 RLS setup")
