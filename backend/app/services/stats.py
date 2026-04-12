from supabase import Client
from app.models.schemas import StatsResponse
import logging

logger = logging.getLogger(__name__)


async def get_stats(db: Client) -> StatsResponse:
    """
    Aggregate stats: total hs_codes, total searches, total regulations,
    and top 10 most popular search queries.
    """
    total_hs = 0
    total_searches = 0
    total_regulations = 0
    popular_queries: list[dict] = []

    try:
        r = db.table("hs_codes").select("id", count="exact").eq("is_active", True).execute()
        total_hs = r.count or 0
    except Exception as e:
        logger.warning(f"stats: hs_codes count failed: {e}")

    try:
        r = db.table("search_history").select("id", count="exact").execute()
        total_searches = r.count or 0
    except Exception as e:
        logger.warning(f"stats: search_history count failed: {e}")

    try:
        r = (
            db.table("customs_regulations")
            .select("id", count="exact")
            .eq("is_active", True)
            .execute()
        )
        total_regulations = r.count or 0
    except Exception as e:
        logger.warning(f"stats: regulations count failed: {e}")

    try:
        # Get most recent 500 queries and count manually (Supabase free tier lacks GROUP BY)
        r = (
            db.table("search_history")
            .select("query")
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )
        rows = r.data or []
        from collections import Counter
        counts = Counter(row["query"] for row in rows)
        popular_queries = [
            {"query": q, "count": c}
            for q, c in counts.most_common(10)
        ]
    except Exception as e:
        logger.warning(f"stats: popular queries failed: {e}")

    return StatsResponse(
        total_hs_codes=total_hs,
        total_searches=total_searches,
        total_regulations=total_regulations,
        popular_queries=popular_queries,
    )
