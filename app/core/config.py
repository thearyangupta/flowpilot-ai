from functools import lru_cache

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    app_name: str = "FlowPilot AI"
    environment: str = "development"

    database_url: str
    test_database_url: str = ""

    gemini_backend: str = "api_key"
    gemini_api_key: str
    gemini_model: str = "gemini-3.5-flash"

    google_cloud_project: str = ""
    google_cloud_location: str = "global"

    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    streamlit_app_url: str = "http://localhost:8501"

    gmail_poll_query: str = ""

    r2_endpoint_url: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "flowpilot-knowledge"

    redis_broker_url: str = "redis://localhost:6379/0"
    redis_result_url: str = "redis://localhost:6379/1"

    redis_rate_limit_url: str = "redis://localhost:6379/2"

    execution_create_rate_limit: int = 10
    execution_create_rate_window_seconds: int = 60

    jwt_secret: str
    jwt_issuer: str = "flowpilot-api"
    jwt_audience: str = "flowpilot-client"
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 15

    auth_cookie_name: str = "flowpilot_session"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "lax"

    token_encryption_keys: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()