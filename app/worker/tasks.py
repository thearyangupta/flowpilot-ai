from uuid import UUID

from app.db.session import SessionLocal
from app.models.execution import Execution
from app.services.execution_event_service import create_execution_event
from app.services.workflow_runner import run
from app.worker.celery_app import celery_app
from app.core.exceptions import RetryableExecutionError

import random
from math import pow

@celery_app.task(
    bind=True,
    name="flowpilot.run_execution",
    acks_late=True,
    reject_on_worker_lost=True,
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
    except RetryableExecutionError as exc:

        db.rollback()

        retry_count = self.request.retries
        countdown = (2 ** retry_count) + random.uniform(0, 1)
        
        raise self.retry(
            exc=exc,
            countdown=countdown,
            max_retries=5,
            )
    
    except Exception:
        db.rollback()
        raise

    finally:
        db.close()