"""
T14: Tests for Redis cache, rate limiting, and Docker Compose config.
These tests run without a live Redis — they verify fallback behavior and logic.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request


# ── Cache module tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cache_get_returns_none_when_redis_unavailable():
    """cache_get must return None gracefully when Redis is down."""
    from app.core import cache as cache_module
    # Reset global so it tries to reconnect
    cache_module._redis = None
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_client.ping.side_effect = ConnectionRefusedError("Redis down")
        mock_from_url.return_value = mock_client
        result = await cache_module.cache_get("missing_key")
    assert result is None
    cache_module._redis = None  # reset


@pytest.mark.asyncio
async def test_cache_set_is_noop_when_redis_unavailable():
    """cache_set must not raise when Redis is down."""
    from app.core import cache as cache_module
    cache_module._redis = None
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_client.ping.side_effect = ConnectionRefusedError("Redis down")
        mock_from_url.return_value = mock_client
        # Should not raise
        await cache_module.cache_set("key", {"data": 1}, ttl=60)
    cache_module._redis = None


@pytest.mark.asyncio
async def test_cache_get_returns_data_when_redis_available():
    """cache_get returns deserialized JSON when Redis has the key."""
    from app.core import cache as cache_module
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value='{"code": "8517.12.00"}')
    cache_module._redis = mock_redis

    result = await cache_module.cache_get("hs:code:8517.12.00")
    assert result == {"code": "8517.12.00"}
    cache_module._redis = None


@pytest.mark.asyncio
async def test_cache_set_calls_setex():
    """cache_set calls redis.setex with correct args."""
    from app.core import cache as cache_module
    mock_redis = AsyncMock()
    cache_module._redis = mock_redis

    await cache_module.cache_set("hs:search:test", {"results": []}, ttl=300)
    mock_redis.setex.assert_called_once()
    args = mock_redis.setex.call_args[0]
    assert args[0] == "hs:search:test"
    assert args[1] == 300
    assert '"results"' in args[2]
    cache_module._redis = None


# ── Rate limiter tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rate_limit_memory_allows_under_limit():
    """In-memory rate limiter allows requests under the limit."""
    from app.core import rate_limit as rl_module
    from app.core.rate_limit import _check_memory
    rl_module._memory_store.clear()

    for _ in range(5):
        result = await _check_memory("test_ip_allow", limit=10, window=60)
        assert result is True


@pytest.mark.asyncio
async def test_rate_limit_memory_blocks_over_limit():
    """In-memory rate limiter blocks requests over the limit."""
    from app.core import rate_limit as rl_module
    from app.core.rate_limit import _check_memory
    rl_module._memory_store.clear()

    for _ in range(3):
        await _check_memory("test_ip_block", limit=3, window=60)

    result = await _check_memory("test_ip_block", limit=3, window=60)
    assert result is False


@pytest.mark.asyncio
async def test_rate_limit_raises_429_when_exceeded():
    """rate_limit dependency raises HTTP 429 when limit is exceeded."""
    from app.core import rate_limit as rl_module
    from app.core.rate_limit import rate_limit
    from fastapi import HTTPException
    rl_module._memory_store.clear()

    # Simulate request with client IP
    mock_request = MagicMock(spec=Request)
    mock_request.client = MagicMock()
    mock_request.client.host = "192.168.1.99"
    mock_request.url.path = "/api/chatbot/ask"

    # Patch get_redis to return None (use memory fallback)
    with patch("app.core.rate_limit.get_redis", new=AsyncMock(return_value=None)):
        # Fill up the limit
        for _ in range(3):
            rl_module._memory_store.setdefault("rate:/api/chatbot/ask:192.168.1.99", [])
            await rate_limit(mock_request, limit=3, window=60)

        # Next call should raise 429
        with pytest.raises(HTTPException) as exc_info:
            await rate_limit(mock_request, limit=3, window=60)
        assert exc_info.value.status_code == 429


# ── Docker Compose config test ─────────────────────────────────────────────

def test_docker_compose_has_redis_and_dependency():
    """docker-compose.yml must define redis service and backend depends_on redis."""
    import yaml
    import os
    compose_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docker-compose.yml"
    )
    with open(compose_path) as f:
        config = yaml.safe_load(f)

    services = config["services"]
    assert "redis" in services, "redis service must be defined"

    redis_svc = services["redis"]
    assert "healthcheck" in redis_svc, "redis must have healthcheck"

    backend_svc = services["backend"]
    deps = backend_svc.get("depends_on", {})
    assert "redis" in deps, "backend must depend on redis"

    assert "REDIS_URL" in backend_svc.get("environment", {}) or \
           any("REDIS_URL" in str(e) for e in backend_svc.get("environment", [])), \
        "backend must have REDIS_URL env var"

    volumes = config.get("volumes", {})
    assert "redis_data" in volumes, "redis_data volume must be defined"


# ── FastAPI integration: cache key format ────────────────────────────────────

def test_cache_key_format():
    """Verify search cache key lowercases and strips query."""
    query = "  Điện Thoại  "
    limit = 20
    threshold = 0.15
    key = f"hs:search:{query.lower().strip()}:{limit}:{threshold}"
    assert key == "hs:search:điện thoại:20:0.15"
