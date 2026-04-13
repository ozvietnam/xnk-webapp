from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # Ollama (local LLM, fallback)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-coder:32b"

    # Gemini (production LLM, preferred when key is set)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # App
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    # Accept comma-separated string or JSON list from env
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Redis (T14)
    REDIS_URL: str = "redis://localhost:6379"

    # Database direct URL (optional, used by migration scripts)
    DATABASE_URL: str = ""

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()
