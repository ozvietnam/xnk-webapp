from fastapi import APIRouter, Depends
from supabase import Client
from app.core.deps import get_db
from app.models.schemas import StatsResponse
from app.services import stats as stats_service

router = APIRouter()


@router.get("/", response_model=StatsResponse)
async def get_stats(db: Client = Depends(get_db)):
    return await stats_service.get_stats(db)
