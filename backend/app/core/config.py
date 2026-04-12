from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # Claude API
    CLAUDE_API_KEY: str = ""

    # App
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Redis (T14)
    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
