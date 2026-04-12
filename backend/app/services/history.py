from supabase import Client
from app.models.schemas import SearchHistoryItem
from typing import List
import logging

logger = logging.getLogger(__name__)


async def get_user_history(
    db: Client, user_id: str, limit: int = 50
) -> List[SearchHistoryItem]:
    """
    Fetch search history for a specific user.
    Uses service_role client (db) — RLS bypassed at service layer.
    """
    try:
        response = (
            db.table("search_history")
            .select("id,query,result_codes,created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [SearchHistoryItem(**row) for row in (response.data or [])]
    except Exception as e:
        logger.error(f"get_user_history({user_id}) failed: {e}")
        return []


async def record_search(
    db: Client,
    query: str,
    result_codes: list[str],
    user_id: str | None = None,
    user_session: str | None = None,
) -> None:
    """Insert a search history record. Called by T05 chatbot service."""
    try:
        row = {
            "query": query,
            "result_codes": result_codes,
        }
        if user_id:
            row["user_id"] = user_id
        if user_session:
            row["user_session"] = user_session

        db.table("search_history").insert(row).execute()
    except Exception as e:
        logger.warning(f"record_search failed (non-fatal): {e}")
