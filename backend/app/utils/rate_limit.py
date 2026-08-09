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
    def __init__(self, max_keys: int = 10_000) -> None:
        self._windows: dict[tuple[str, str], tuple[float, int]] = {}
        self._lock = Lock()
        self._max_keys = max_keys
        self._checks = 0

    def _evict(self, now: float) -> None:
        expired = [key for key, (reset_at, _) in self._windows.items() if reset_at <= now]
        for key in expired:
            self._windows.pop(key, None)
        overflow = len(self._windows) - self._max_keys
        if overflow > 0:
            for key, _ in sorted(self._windows.items(), key=lambda item: item[1][0])[:overflow]:
                self._windows.pop(key, None)

    def check(
        self, request: Request, bucket: str, limit: int, window_seconds: int = 60,
        identity: str | None = None,
    ) -> None:
        client = identity or (request.client.host if request.client else "unknown")
        key = (bucket, client)
        now = monotonic()
        with self._lock:
            self._checks += 1
            if self._checks % 128 == 0:
                self._evict(now)
            if key not in self._windows and len(self._windows) >= self._max_keys:
                oldest = min(self._windows, key=lambda item: self._windows[item][0])
                self._windows.pop(oldest, None)
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
