from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_fallback_model: str = "qwen/qwen3.6-27b"

    database_url: str = "sqlite:///./hcp_crm.db"

    cors_origins: str = "http://localhost:5173"
    env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def cors_origin_list(self):
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()