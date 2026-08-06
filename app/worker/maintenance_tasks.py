from datetime import timedelta

from app.db.session import SessionLocal
from app.services.execution.execution_maintenance_service import (
    find_stale_executions,
)
from app.worker.celery_app import celery_app
from app.worker.tasks import run_execution_task


@celery_app.task(
    name="flowpilot.maintenance.recover_stale",
)
def recover_stale() -> dict[str, int]:
    db = SessionLocal()

    try:
        stale_executions = find_stale_executions(
            db=db,
            stale_after=timedelta(minutes=5),
        )

        for execution in stale_executions:
            run_execution_task.delay(
                str(execution.id)
            )

        return {
            "queued": len(stale_executions),
        }

    finally:
        db.close()


@celery_app.task(
    name="flowpilot.maintenance.expire_results",
)
def expire_results() -> dict[str, int]:
    return {
        "expired": 0,
    }