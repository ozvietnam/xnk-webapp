from supabase import Client
from app.models.schemas import RegulationResponse
from typing import List, Optional


async def list_regulations(
    db: Client, category: Optional[str], limit: int
) -> List[RegulationResponse]:
    raise NotImplementedError("Requires T02 schema + Supabase connection")


async def get_by_id(db: Client, regulation_id: int) -> Optional[RegulationResponse]:
    raise NotImplementedError("Requires T02 schema + Supabase connection")
