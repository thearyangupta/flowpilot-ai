from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings


settings = get_settings()

celery_app = Celery(
    "flowpilot",
    broker=settings.redis_broker_url,
    backend=settings.redis_result_url,
    include=["app.worker.tasks",
             "app.worker.maintenance_tasks",
             "app.worker.gmail_tasks",
             ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_default_queue="workflows",
    task_routes={
        "flowpilot.run_execution": {
            "queue": "workflows",
        },
        "flowpilot.maintenance.*": {
            "queue": "maintenance",
        },
    },
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "recover-stale-executions": {
        "task": "flowpilot.maintenance.recover_stale",
        "schedule": 60.0,
        "options": {
            "queue": "maintenance",
        },
    },

    "poll-connected-gmail": {
        "task": "flowpilot.gmail.poll_connected_accounts",
        "schedule": 120.0,
        "options": {
            "queue": "maintenance",
        },
    },

    "expire-old-task-results": {
        "task": "flowpilot.maintenance.expire_results",
        "schedule": crontab(
            hour=2,
            minute=0,
        ),
        "options": {
            "queue": "maintenance",
        },
    },
}