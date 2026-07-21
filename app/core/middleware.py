from time import perf_counter
from uuid import uuid4

from fastapi import Request

from app.core.logging import get_logger


logger = get_logger(__name__)


async def request_id_middleware(
    request: Request,
    call_next,
):
    request_id = str(uuid4())
    request.state.request_id = request_id

    start_time = perf_counter()

    logger.info(
        "request_started request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
    )

    response = await call_next(request)

    duration_ms = (perf_counter() - start_time) * 1000

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "request_completed request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response