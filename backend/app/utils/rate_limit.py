"""Small process-local limiter for abuse-sensitive endpoints.

Production deployments must add a shared edge/global limiter. This helper is a
last-mile control that prevents a single worker from accepting an unbounded
burst and keeps the application usable without an optional dependency.
"""

from collections import defaultdict
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status


class _WindowLimiter:
    def __init__(self) -> None:
        self._windows: dict[tuple[str, str], tuple[float, int]] = {}
        self._lock = Lock()

    def check(self, request: Request, bucket: str, limit: int, window_seconds: int = 60) -> None:
        client = request.client.host if request.client else "unknown"
        key = (bucket, client)
        now = monotonic()
        with self._lock:
            reset_at, count = self._windows.get(key, (now + window_seconds, 0))
            if now >= reset_at:
                reset_at, count = now + window_seconds, 0
            if count >= limit:
                retry_after = max(1, int(reset_at - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )
            self._windows[key] = (reset_at, count + 1)


limiter = _WindowLimiter()
