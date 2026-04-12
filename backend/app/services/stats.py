from supabase import Client
from app.models.schemas import StatsResponse


async def get_stats(db: Client) -> StatsResponse:
    raise NotImplementedError("Requires T02 schema + Supabase connection")
