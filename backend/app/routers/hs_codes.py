from fastapi import APIRouter, Depends, Query, HTTPException
from supabase import Client
from app.core.deps import get_db
from app.models.schemas import HSCodeResponse, HSCodeSearchResult, HSSearchResponse
from app.services import hs_search as hs_search_service

router = APIRouter()


@router.get("/search", response_model=HSSearchResponse)
async def search_hs_codes(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    threshold: float = Query(0.15, ge=0.0, le=1.0, description="pg_trgm similarity threshold"),
    db: Client = Depends(get_db),
):
    results = await hs_search_service.search(db, q, limit, threshold)
    return HSSearchResponse(results=results, total=len(results), query=q)


@router.get("/{code}", response_model=HSCodeResponse)
async def get_hs_code(code: str, db: Client = Depends(get_db)):
    result = await hs_search_service.get_by_code(db, code)
    if not result:
        raise HTTPException(status_code=404, detail=f"HS code {code} not found")
    return result
