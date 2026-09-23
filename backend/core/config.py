"""Application settings for the HydroSentinel backend."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic import model_validator
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
    bootstrap_admin_enabled: bool = False
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_name: str = "HydroSentinel Admin"
    allow_public_registration: bool | None = None
    demo_rate_limit_requests: int = 12
    demo_rate_limit_window_seconds: int = 60
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    cors_origin_regex: str | None = r"https://hydro-sentinel-water-leak-detection(?:-25nt-[a-z0-9]+-hydro5|-xi)\.vercel\.app"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env.lower() != "production":
            return self

        normalized_secret = self.jwt_secret_key.strip().lower()
        if (
            len(self.jwt_secret_key.strip()) < 32
            or normalized_secret in {"", "change-me", "secret", "placeholder"}
            or normalized_secret.startswith("change-me")
            or normalized_secret.startswith("your-")
        ):
            raise ValueError("Production JWT configuration is missing or unsafe.")

        if self.bootstrap_admin_enabled:
            password = self.bootstrap_admin_password or ""
            normalized_password = password.strip().lower()
            if (
                not self.bootstrap_admin_email
                or len(password) < 12
                or normalized_password in {"changeme123!", "change-me", "password", "admin"}
                or normalized_password.startswith("change-me")
            ):
                raise ValueError("Production bootstrap administrator configuration is incomplete or unsafe.")

        return self

    @property
    def public_registration_enabled(self) -> bool:
        if self.allow_public_registration is not None:
            return self.allow_public_registration
        return self.app_env.lower() != "production"

    @property
    def resolved_data_root(self) -> Path:
        return self.data_root or self.project_root

    @property
    def resolved_model_path(self) -> Path:
        return self.model_path or (self.project_root / "hydrosentinel_isolation_forest.joblib")

    def resolved_diagnostic_model_path(self, event_mode: bool) -> Path:
        """Keep Standard and Event diagnostic artifacts physically independent."""
        base = self.resolved_model_path
        mode = "event" if event_mode else "standard"
        return base.with_name(f"{base.stem}_{mode}{base.suffix}")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
