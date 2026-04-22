from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@db:5432/martin"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    sql_dir: Path = PROJECT_ROOT / "sql"
    data_dir: Path = PROJECT_ROOT / "data"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_name(self) -> str:
        database_name = urlparse(self.database_url).path.lstrip("/")
        if not database_name:
            raise ValueError("DATABASE_URL must include a database name")
        return database_name


@lru_cache
def get_settings() -> Settings:
    return Settings()