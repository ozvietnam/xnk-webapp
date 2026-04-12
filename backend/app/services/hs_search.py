from supabase import Client
from app.models.schemas import HSCodeResponse
from typing import List, Optional


async def search(db: Client, query: str, limit: int = 20) -> List[HSCodeResponse]:
    """
    Search HS codes using pg_trgm similarity on description_vi.
    Falls back to ILIKE if similarity returns no results.
    Implemented via Supabase RPC calling a DB function.
    """
    # T04 will implement the actual pg_trgm RPC call.
    # Placeholder until T02 (schema) and T03 (seed) are done.
    raise NotImplementedError("Requires T02 schema + T03 seed data + Supabase connection")


async def get_by_code(db: Client, code: str) -> Optional[HSCodeResponse]:
    """Get a single HS code by exact code match."""
    raise NotImplementedError("Requires T02 schema + Supabase connection")
