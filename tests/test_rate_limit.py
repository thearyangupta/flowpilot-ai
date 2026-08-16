from uuid import uuid4

from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.routers import executions
from app.core.config import get_settings
from app.core.rate_limit import (
    RateLimitExceeded,
    RedisRateLimiter,
)
from app.main import app
from app.models.user import User


def test_rate_limit_is_shared_across_instances() -> None:
    settings = get_settings()

    redis_a = Redis.from_url(
        settings.redis_rate_limit_url,
        decode_responses=True,
    )

    redis_b = Redis.from_url(
        settings.redis_rate_limit_url,
        decode_responses=True,
    )

    limiter_a = RedisRateLimiter(
        redis_a,
        namespace="flowpilot:test-rate",
    )

    limiter_b = RedisRateLimiter(
        redis_b,
        namespace="flowpilot:test-rate",
    )

    user_id = uuid4()
    route = f"execution:{uuid4()}"

    key = limiter_a.key_for(
        user_id=user_id,
        route_name=route,
    )

    redis_a.delete(key)

    try:
        first = limiter_a.consume(
            user_id=user_id,
            route_name=route,
            limit=3,
            window_seconds=30,
        )

        second = limiter_b.consume(
            user_id=user_id,
            route_name=route,
            limit=3,
            window_seconds=30,
        )

        third = limiter_a.consume(
            user_id=user_id,
            route_name=route,
            limit=3,
            window_seconds=30,
        )

        fourth = limiter_b.consume(
            user_id=user_id,
            route_name=route,
            limit=3,
            window_seconds=30,
        )

        assert first.allowed is True
        assert second.allowed is True
        assert third.allowed is True
        assert fourth.allowed is False

        assert 1 <= fourth.retry_after <= 30

    finally:
        redis_a.delete(key)


def test_user_b_has_independent_budget() -> None:
    settings = get_settings()

    redis_client = Redis.from_url(
        settings.redis_rate_limit_url,
        decode_responses=True,
    )

    limiter = RedisRateLimiter(
        redis_client,
        namespace="flowpilot:test-rate",
    )

    user_a = uuid4()
    user_b = uuid4()
    route = f"execution:{uuid4()}"

    key_a = limiter.key_for(
        user_id=user_a,
        route_name=route,
    )

    key_b = limiter.key_for(
        user_id=user_b,
        route_name=route,
    )

    redis_client.delete(
        key_a,
        key_b,
    )

    try:
        limiter.consume(
            user_id=user_a,
            route_name=route,
            limit=1,
            window_seconds=30,
        )

        blocked = limiter.consume(
            user_id=user_a,
            route_name=route,
            limit=1,
            window_seconds=30,
        )

        user_b_result = limiter.consume(
            user_id=user_b,
            route_name=route,
            limit=1,
            window_seconds=30,
        )

        assert blocked.allowed is False
        assert user_b_result.allowed is True

    finally:
        redis_client.delete(
            key_a,
            key_b,
        )


def test_http_429_has_retry_after(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    user = User(
        email=f"rate-{uuid4()}@example.com",
        display_name="Rate Limit",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    app.dependency_overrides[
        get_current_user
    ] = lambda: user

    def blocked(**kwargs):
        raise RateLimitExceeded(
            retry_after=17
        )

    monkeypatch.setattr(
        executions,
        "enforce_rate_limit",
        blocked,
    )

    response = client.post(
        (
            f"/api/v1/projects/{uuid4()}"
            f"/workflows/{uuid4()}"
            "/executions"
        ),
        json={
            "input_data": {},
            "idempotency_key":
                "rate-test-request",
        },
    )

    assert response.status_code == 429

    assert response.headers[
        "Retry-After"
    ] == "17"

    assert response.json() == {
        "detail":
            "Rate limit exceeded. "
            "Please try again later."
    }