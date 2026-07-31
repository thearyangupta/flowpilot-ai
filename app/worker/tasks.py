from uuid import UUID

from app.db.session import SessionLocal
from app.models.execution import Execution
from app.services.execution_event_service import create_execution_event
from app.services.workflow_runner import run
from app.worker.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="flowpilot.run_execution",
)
def run_execution_task(
    self,
    execution_id: str,
) -> None:
    db = SessionLocal()

    try:
        execution_uuid = UUID(execution_id)

        execution = db.get(
            Execution,
            execution_uuid,
        )

        if execution is None:
            return

        create_execution_event(
            db=db,
            execution_id=execution.id,
            event_type="execution.worker_started",
            details={
                "celery_task_id": self.request.id,
            },
            actor="celery_worker",
        )

        db.commit()

        run(
            db=db,
            execution=execution,
            initial_context=dict(execution.input_data or {}),
        )
    except Exception:
        db.rollback()
        raise

    finally:
        db.close()