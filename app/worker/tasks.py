from app.worker.celery_app import celery_app


@celery_app.task(name="flowpilot.debug")
def debug_task() -> str:
    return "worker is running"