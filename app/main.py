from fastapi import FastAPI, HTTPException, status
from redis import Redis
from sqlalchemy import text

from app.api.router import router
from app.core.config import get_settings
from app.core.middleware import request_id_middleware
from app.db.session import engine


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
    )

    app.middleware("http")(request_id_middleware)

    app.include_router(
        router,
        prefix="/api/v1",
    )

    @app.get(
        "/health",
        tags=["system"],
    )
    def health() -> dict[str, str]:
        """
        Process-level liveness.

        This endpoint deliberately does not test external
        dependencies. It answers only whether the API process
        is alive and serving requests.
        """
        return {
            "status": "ok",
            "service": "flowpilot-api",
        }

    @app.get(
        "/ready",
        tags=["system"],
    )
    def readiness() -> dict[str, str]:
        """
        Dependency-aware readiness.

        FlowPilot is ready only when PostgreSQL and Redis are
        reachable. Do not expose connection details or secrets
        in the response.
        """

        try:
            with engine.connect() as connection:
                connection.execute(
                    text("SELECT 1")
                )

            redis_client = Redis.from_url(
                settings.redis_broker_url,
                socket_connect_timeout=2,
                socket_timeout=2,
            )

            try:
                redis_client.ping()
            finally:
                redis_client.close()

        except Exception as error:
            raise HTTPException(
                status_code=(
                    status.HTTP_503_SERVICE_UNAVAILABLE
                ),
                detail="FlowPilot dependencies are not ready.",
            ) from error

        return {
            "status": "ready",
            "service": "flowpilot-api",
        }

    return app


app = create_app()
