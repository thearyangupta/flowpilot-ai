from dataclasses import dataclass
from functools import lru_cache
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings


RATE_LIMIT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

local ttl = redis.call("TTL", KEYS[1])

if ttl < 0 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
    ttl = tonumber(ARGV[1])
end

return {current, ttl}
"""


@dataclass(frozen=True)
class RateLimitDecision:
    count: int
    limit: int
    retry_after: int

    @property
    def allowed(self) -> bool:
        return self.count <= self.limit


class RateLimitError(Exception):
    pass


class RateLimitExceeded(RateLimitError):
    def __init__(
        self,
        *,
        retry_after: int,
    ) -> None:
        self.retry_after = max(
            1,
            retry_after,
        )

        super().__init__(
            "Rate limit exceeded."
        )


class RateLimitUnavailable(RateLimitError):
    pass


class RedisRateLimiter:
    def __init__(
        self,
        redis_client: Redis,
        *,
        namespace: str = "flowpilot:rate",
    ) -> None:
        self.redis = redis_client
        self.namespace = namespace

    def key_for(
        self,
        *,
        user_id: UUID,
        route_name: str,
    ) -> str:
        safe_route = route_name.replace(
            " ",
            "_",
        )

        return (
            f"{self.namespace}:"
            f"{user_id}:"
            f"{safe_route}"
        )

    def consume(
        self,
        *,
        user_id: UUID,
        route_name: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        if limit < 1:
            raise ValueError(
                "Rate limit must be at least 1."
            )

        if window_seconds < 1:
            raise ValueError(
                "Rate-limit window must be "
                "at least 1 second."
            )

        key = self.key_for(
            user_id=user_id,
            route_name=route_name,
        )

        try:
            result = self.redis.eval(
                RATE_LIMIT_SCRIPT,
                1,
                key,
                window_seconds,
            )

        except RedisError as error:
            raise RateLimitUnavailable(
                "Rate limiting storage is unavailable."
            ) from error

        count = int(result[0])
        retry_after = max(
            1,
            int(result[1]),
        )

        return RateLimitDecision(
            count=count,
            limit=limit,
            retry_after=retry_after,
        )


@lru_cache
def get_rate_limiter() -> RedisRateLimiter:
    settings = get_settings()

    client = Redis.from_url(
        settings.redis_rate_limit_url,
        decode_responses=True,
    )

    return RedisRateLimiter(client)


def enforce_rate_limit(
    *,
    user_id: UUID,
    route_name: str,
    limit: int,
    window_seconds: int,
) -> RateLimitDecision:
    decision = get_rate_limiter().consume(
        user_id=user_id,
        route_name=route_name,
        limit=limit,
        window_seconds=window_seconds,
    )

    if not decision.allowed:
        raise RateLimitExceeded(
            retry_after=decision.retry_after,
        )

    return decision