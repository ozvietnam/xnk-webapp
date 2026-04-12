from supabase import Client
from app.models.schemas import RegulationResponse
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"thu-tuc", "chung-tu", "thue", "kiem-tra"}


async def list_regulations(
    db: Client,
    category: Optional[str],
    limit: int,
) -> List[RegulationResponse]:
    try:
        query = (
            db.table("customs_regulations")
            .select("id,category,title,content_vi,effective_date,source_document,tags,created_at")
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(limit)
        )
        if category:
            query = query.eq("category", category)

        response = query.execute()
        return [RegulationResponse(**row) for row in (response.data or [])]

    except Exception as e:
        logger.error(f"list_regulations failed: {e}")
        return []


async def get_by_id(db: Client, regulation_id: str) -> Optional[RegulationResponse]:
    try:
        response = (
            db.table("customs_regulations")
            .select("id,category,title,content_vi,effective_date,source_document,tags,created_at")
            .eq("id", regulation_id)
            .eq("is_active", True)
            .single()
            .execute()
        )
        if response.data:
            return RegulationResponse(**response.data)
        return None
    except Exception as e:
        logger.error(f"get_by_id({regulation_id}) failed: {e}")
        return None
