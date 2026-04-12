from fastapi import APIRouter, Depends
from supabase import Client
from app.core.deps import get_service_db, require_auth
from app.models.schemas import SearchHistoryItem
from app.services import history as history_service
from typing import List

router = APIRouter()


@router.get("/", response_model=List[SearchHistoryItem])
async def get_history(
    db: Client = Depends(get_service_db),
    user_id: str = Depends(require_auth),
):
    return await history_service.get_user_history(db, user_id)
