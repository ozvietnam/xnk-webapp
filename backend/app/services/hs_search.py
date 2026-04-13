from supabase import Client
from app.models.schemas import HSCodeResponse, HSCodeSearchResult
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


async def search(
    db: Client,
    query: str,
    limit: int = 20,
    threshold: float = 0.10,  # lowered from 0.15 — handles queries without diacritics
) -> List[HSCodeSearchResult]:
    """
    Search HS codes using the search_hs_codes() PostgreSQL RPC function.
    Falls back to ILIKE-only search if RPC returns 0 results or fails.
    """
    try:
        response = db.rpc(
            "search_hs_codes",
            {
                "search_query": query,
                "result_limit": limit,
                "sim_threshold": threshold,
            },
        ).execute()

        if response.data:
            return [HSCodeSearchResult(**row) for row in response.data]

        # RPC returned empty — fall through to ILIKE for better coverage
        logger.info(f"RPC returned 0 results for '{query}', trying ILIKE fallback")

    except Exception as e:
        logger.warning(f"RPC search_hs_codes failed ({e}), falling back to ILIKE")

    return await _ilike_fallback(db, query, limit)


async def _ilike_fallback(
    db: Client, query: str, limit: int
) -> List[HSCodeSearchResult]:
    """Direct ILIKE search on description_vi and code as fallback."""
    try:
        response = (
            db.table("hs_codes")
            .select("id,code,description_vi,description_en,unit,tax_rate_normal,tax_rate_preferential,tax_rate_special,notes")
            .eq("is_active", True)
            .ilike("description_vi", f"%{query}%")
            .limit(limit)
            .execute()
        )
        rows = response.data or []

        # Also search by code prefix
        code_response = (
            db.table("hs_codes")
            .select("id,code,description_vi,description_en,unit,tax_rate_normal,tax_rate_preferential,tax_rate_special,notes")
            .eq("is_active", True)
            .ilike("code", f"{query}%")
            .limit(limit)
            .execute()
        )
        code_rows = code_response.data or []

        # Merge and deduplicate by id
        seen = set()
        combined = []
        for row in rows + code_rows:
            if row["id"] not in seen:
                seen.add(row["id"])
                combined.append(HSCodeSearchResult(**row, similarity_score=None))

        return combined[:limit]

    except Exception as e:
        logger.error(f"ILIKE fallback also failed: {e}")
        return []


async def get_by_code(db: Client, code: str) -> Optional[HSCodeResponse]:
    """Get a single HS code by exact code match."""
    try:
        response = (
            db.table("hs_codes")
            .select("*")
            .eq("code", code)
            .eq("is_active", True)
            .single()
            .execute()
        )
        if response.data:
            return HSCodeResponse(**response.data)
        return None
    except Exception as e:
        logger.error(f"get_by_code({code}) failed: {e}")
        return None
