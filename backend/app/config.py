from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AIVIS"
    upload_dir: Path = Field(default=Path("uploads"), alias="AIVIS_UPLOAD_DIR")
    database_path: Path = Field(default=Path("storage/aivis.db"), alias="AIVIS_DATABASE_PATH")
    preprocess_dir: Path = Field(default=Path("storage/preprocess"), alias="AIVIS_PREPROCESS_DIR")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
        alias="AIVIS_CORS_ORIGINS",
    )
    task_executor: str = Field(default="background", alias="AIVIS_TASK_EXECUTOR")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="AIVIS_CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", alias="AIVIS_CELERY_RESULT_BACKEND")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    settings.preprocess_dir.mkdir(parents=True, exist_ok=True)
    return settings
