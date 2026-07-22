"""Application configuration loaded from environment variables.

Keeping deployment-specific values in one settings object prevents secrets,
provider URLs, and model names from being hard-coded across the application.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Core application settings.
    app_name: str = "MusicPulse AI"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./musicpulse.db"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # YouTube collection settings.
    youtube_api_key: str = ""
    default_region: str = "KE"
    music_category_id: str = "10"
    popular_fetch_size: int = 25
    recent_fetch_hours: int = 24

    # Gemini is used only for grounded natural-language answer generation.
    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_chat_model: str = "gemini-2.5-flash"
    llm_enabled: bool = True
    llm_timeout_seconds: int = 60

    # BGE runs locally and does not require a paid embeddings API.
    bge_embedding_model: str = "BAAI/bge-small-en-v1.5"
    bge_device: str = "cpu"
    bge_enabled: bool = True
    rag_top_k: int = 5
    # bge-small-en-v1.5 produces 384-dimensional vectors.
    rag_embedding_dimensions: int = 384

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """Return a clean list suitable for FastAPI's CORS middleware."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def llm_available(self) -> bool:
        """Gemini calls are possible only when the feature and API key are enabled."""
        return self.llm_enabled and bool(self.gemini_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for dependency-free application use."""
    return Settings()
