from app.worker.celery_app import celery_app


@celery_app.task(
    name="flowpilot.gmail.poll_connected_accounts",
)
def poll_connected_accounts() -> None:
    return None