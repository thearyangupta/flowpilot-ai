from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FlowPilot AI"
    environment: str = "development"

    database_url: str
    test_database_url: str

    gemini_api_key: str
    gemini_model: str = "gemini-3.5-flash"

    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    redis_broker_url: str = "redis://localhost:6379/0"
    redis_result_url: str = "redis://localhost:6379/1"

    jwt_secret: str
    jwt_issuer: str = "flowpilot-api"
    jwt_audience: str = "flowpilot-client"
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 15

    token_encryption_keys: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()