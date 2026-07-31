from celery import Celery

from app.core.config import get_settings


settings = get_settings()

celery_app = Celery(
    "flowpilot",
    broker=settings.redis_broker_url,
    backend=settings.redis_result_url,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_default_queue="workflows",
    task_routes={
        "flowpilot.run_execution": {"queue": "workflows"},
        "flowpilot.maintenance.*": {"queue": "maintenance"},
    },
    worker_prefetch_multiplier=1,
)