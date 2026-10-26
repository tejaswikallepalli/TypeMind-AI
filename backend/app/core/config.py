"""Application configuration module using pydantic-settings."""

from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """TypeMind AI backend settings and environment variable bindings."""

    # Application Information
    app_name: str = Field(default="TypeMind AI", validation_alias="APP_NAME")
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    debug: bool = Field(default=True, validation_alias="DEBUG")

    # API Routing
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")

    # Server Network
    host: str = Field(default="127.0.0.1", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")

    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # CORS Origins (default supports local web development)
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
        validation_alias="CORS_ORIGINS"
    )

    # Machine Learning Settings
    ml_model_path: str = Field(default="app/ml/artifacts/type_classifier.joblib", validation_alias="ML_MODEL_PATH")
    min_confidence_threshold: float = Field(default=0.60, ge=0.0, le=1.0, validation_alias="MIN_CONFIDENCE_THRESHOLD")

    # Request validation limits
    max_source_size_bytes: int = Field(default=500_000, ge=1_000, validation_alias="MAX_SOURCE_SIZE_BYTES")

    # Supported Python analysis version
    supported_python_version: str = "3.12+"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached instance of application settings."""
    return Settings()
