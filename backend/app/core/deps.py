from fastapi import Header, HTTPException, status
from supabase import Client
from app.core.database import get_client, get_service_client


async def get_db() -> Client:
    return get_client()


async def get_service_db() -> Client:
    return get_service_client()


async def get_current_user_id(authorization: str = Header(None)) -> str | None:
    """Extract user_id from Supabase JWT. Returns None if not authenticated."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        client = get_client()
        user = client.auth.get_user(token)
        return user.user.id if user and user.user else None
    except Exception:
        return None


async def require_auth(authorization: str = Header(None)) -> str:
    """Like get_current_user_id but raises 401 if not authenticated."""
    user_id = await get_current_user_id(authorization)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user_id
