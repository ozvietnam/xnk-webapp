import time
import logging
from fastapi import HTTPException, Request, status
from app.core.cache import get_redis

logger = logging.getLogger(__name__)

# In-memory fallback when Redis is unavailable
_memory_store: dict[str, list[float]] = {}


async def _check_memory(key: str, limit: int, window: int) -> bool:
    """Sliding window rate limiter using in-memory store."""
    now = time.time()
    cutoff = now - window
    hits = [t for t in _memory_store.get(key, []) if t > cutoff]
    if len(hits) >= limit:
        return False
    hits.append(now)
    _memory_store[key] = hits
    return True


async def _check_redis(r, key: str, limit: int, window: int) -> bool:
    """Sliding window rate limiter using Redis sorted set."""
    now = time.time()
    cutoff = now - window
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, cutoff)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window)
    results = await pipe.execute()
    count = results[2]
    return count <= limit


async def rate_limit(request: Request, limit: int = 10, window: int = 60) -> None:
    """
    Rate limit by IP. Raises 429 if exceeded.
    limit: max requests per window
    window: seconds
    """
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate:{request.url.path}:{client_ip}"

    try:
        r = await get_redis()
        if r:
            allowed = await _check_redis(r, key, limit, window)
        else:
            allowed = await _check_memory(key, limit, window)
    except Exception as e:
        logger.warning(f"rate_limit error ({e}) — allowing request")
        allowed = True

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Quá nhiều yêu cầu. Giới hạn {limit} lần/{window}s mỗi IP.",
            headers={"Retry-After": str(window)},
        )
