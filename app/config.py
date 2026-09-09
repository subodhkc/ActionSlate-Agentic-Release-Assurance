"""Runtime configuration and Google Cloud authentication setup."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeConfigurationError(RuntimeError):
    """Raised when the Google runtime cannot be configured safely."""


class Settings(BaseSettings):
    """Application settings loaded from Replit environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    google_cloud_project: str = Field(
        default="actionslate",
        description="Dedicated Google Cloud project ID.",
    )
    google_cloud_location: str = Field(
        default="global",
        description="Vertex AI / Gemini Enterprise Agent Platform location.",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Fast Gemini model suited to structured extraction.",
    )
    google_api_key: str | None = Field(
        default=None,
        validation_alias="GOOGLE_API_KEY",
        repr=False,
    )
    app_name: str = "actionslate"

    @property
    def has_google_credentials(self) -> bool:
        """Return whether the expected Replit secret is present."""

        return bool(self.google_api_key)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings object."""

    return Settings()


def configure_google_runtime(settings: Settings | None = None) -> None:
    """Set the non-secret Vertex AI context used by the Google SDK."""

    settings = settings or get_settings()
    if not settings.google_api_key:
        raise RuntimeConfigurationError(
            "Missing GOOGLE_API_KEY. Add the current Google Cloud authorization "
            "key as a Replit Secret."
        )

    os.environ["GOOGLE_CLOUD_PROJECT"] = settings.google_cloud_project
    os.environ["GOOGLE_CLOUD_LOCATION"] = settings.google_cloud_location