from fastapi import APIRouter, Depends, Query, HTTPException
from supabase import Client
from app.core.deps import get_db
from app.core.cache import cache_get, cache_set
from app.models.schemas import HSCodeResponse, HSCodeSearchResult, HSSearchResponse
from app.services import hs_search as hs_search_service

router = APIRouter()

SEARCH_CACHE_TTL = 300  # 5 minutes
DETAIL_CACHE_TTL = 3600  # 1 hour


@router.get("/search", response_model=HSSearchResponse)
async def search_hs_codes(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    threshold: float = Query(0.15, ge=0.0, le=1.0, description="pg_trgm similarity threshold"),
    db: Client = Depends(get_db),
):
    cache_key = f"hs:search:{q.lower().strip()}:{limit}:{threshold}"
    cached = await cache_get(cache_key)
    if cached:
        results = [HSCodeSearchResult(**r) for r in cached["results"]]
        return HSSearchResponse(results=results, total=cached["total"], query=q)

    results = await hs_search_service.search(db, q, limit, threshold)
    response = HSSearchResponse(results=results, total=len(results), query=q)

    await cache_set(
        cache_key,
        {"results": [r.model_dump() for r in results], "total": len(results)},
        ttl=SEARCH_CACHE_TTL,
    )
    return response


@router.get("/{code}", response_model=HSCodeResponse)
async def get_hs_code(code: str, db: Client = Depends(get_db)):
    cache_key = f"hs:code:{code}"
    cached = await cache_get(cache_key)
    if cached:
        return HSCodeResponse(**cached)

    result = await hs_search_service.get_by_code(db, code)
    if not result:
        raise HTTPException(status_code=404, detail=f"HS code {code} not found")

    await cache_set(cache_key, result.model_dump(), ttl=DETAIL_CACHE_TTL)
    return result
