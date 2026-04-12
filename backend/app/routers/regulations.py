from fastapi import APIRouter, Depends, Query
from supabase import Client
from app.core.deps import get_db
from app.models.schemas import RegulationResponse
from app.services import regulations as reg_service
from typing import List, Optional

router = APIRouter()


@router.get("/", response_model=List[RegulationResponse])
async def list_regulations(
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Client = Depends(get_db),
):
    return await reg_service.list_regulations(db, category, limit)


@router.get("/{regulation_id}", response_model=RegulationResponse)
async def get_regulation(regulation_id: str, db: Client = Depends(get_db)):
    from fastapi import HTTPException
    result = await reg_service.get_by_id(db, regulation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Regulation not found")
    return result
