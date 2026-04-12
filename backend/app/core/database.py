from supabase import create_client, Client
from app.core.config import settings


def get_supabase_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_supabase_service_client() -> Client:
    """Service role client — only for server-side ops requiring elevated privileges."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


# Singleton instances
_client: Client | None = None
_service_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = get_supabase_client()
    return _client


def get_service_client() -> Client:
    global _service_client
    if _service_client is None:
        _service_client = get_supabase_service_client()
    return _service_client
