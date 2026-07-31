from app.worker.celery_app import celery_app


@celery_app.task(name="flowpilot.run_execution")
def run_execution_task(execution_id: str) -> None:
    pass