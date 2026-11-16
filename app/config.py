from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"
    redis_url: str = "redis://localhost:6379/0"
    langsmith_tracing: bool = True
    langsmith_api_key: str | None = None
    langsmith_project: str = "ia-entrega-final"
    max_graph_steps: int = 6
    queue_key: str = "ia-final:jobs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
