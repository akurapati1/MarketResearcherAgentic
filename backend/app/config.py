from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Market Researcher Agentic"
    database_url: str = "sqlite+aiosqlite:///./data/market_researcher.db"

    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-5-5"
    llm_max_tokens: int = 4096
    llm_timeout_seconds: float = 90.0

    max_concurrent_jobs: int = 4
    market_data_mode: str = "auto"  # auto | live | synthetic
    http_timeout_seconds: float = 8.0
    cache_ttl_seconds: int = 300
    rate_limit_per_minute: int = 120
    api_key: str = ""
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
