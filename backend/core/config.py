"""Application settings for the HydroSentinel backend."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HydroSentinel API"
    app_env: str = "development"
    app_debug: bool = True
    api_prefix: str = "/api/v1"
    app_version: str = "1.0.0"
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    data_root: Path | None = None
    model_path: Path | None = None
    database_url: str = "postgresql+psycopg://hydrosentinel:hydrosentinel@postgres:5432/hydrosentinel"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    frontend_origin: str = "http://localhost:3000"
    bootstrap_admin_email: str = "admin@hydrosentinel.app"
    bootstrap_admin_password: str = "ChangeMe123!"
    bootstrap_admin_name: str = "HydroSentinel Admin"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_data_root(self) -> Path:
        return self.data_root or self.project_root

    @property
    def resolved_model_path(self) -> Path:
        return self.model_path or (self.project_root / "hydrosentinel_isolation_forest.joblib")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()