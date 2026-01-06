# app/config.py

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    # Default to SQLite for local dev without Docker
    # Docker/Prod will override this via DATABASE_URL env var
    database_url: str = "sqlite:///./rankings.db"
    database_echo: bool = False
    
    # Seeding
    seed_rankings_on_startup: bool = False

    # API
    api_title: str = "Liella Rankings API"
    api_version: str = "v1"

    # Scheduler
    analysis_scheduler_enabled: bool = True
    analysis_schedule_hour: int = 0
    analysis_schedule_minute: int = 0

    # Paths
    config_dir: Path = Path(__file__).parent / "seeds"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
