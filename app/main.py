from fastapi import FastAPI
from app.core.middleware import request_id_middleware
import app.models.execution
import app.models.project
import app.models.workflow

from app.api.router import router
from app.core.config import get_settings


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

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "flowpilot-api",
            "environment": settings.environment,
        }

    return app


app = create_app()