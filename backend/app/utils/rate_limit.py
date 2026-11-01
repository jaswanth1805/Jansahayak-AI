"""Small process-local sliding-window limits for unauthenticated API routes."""

from collections import defaultdict, deque
from contextlib import asynccontextmanager
import asyncio
import time

from fastapi import HTTPException, Request, status


class SlidingWindowLimit:
    def __init__(self, requests: int, window_seconds: int):
        self.requests = requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def __call__(self, request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        async with self._lock:
            events = self._events[key]
            while events and now - events[0] >= self.window_seconds:
                events.popleft()
            if len(events) >= self.requests:
                retry_after = max(1, int(self.window_seconds - (now - events[0])))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again shortly.",
                    headers={"Retry-After": str(retry_after)},
                )
            events.append(now)
            if len(self._events) > 10_000:
                stale_keys = [
                    client_key for client_key, client_events in self._events.items()
                    if not client_events or now - client_events[-1] >= self.window_seconds
                ]
                for client_key in stale_keys:
                    self._events.pop(client_key, None)


class ConcurrencyGate:
    """Reject excess expensive work instead of queueing unbounded tasks."""
    def __init__(self, maximum_active: int):
        self.maximum_active = maximum_active
        self._active = 0
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def enter(self):
        async with self._lock:
            if self._active >= self.maximum_active:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="The service is busy. Please retry shortly.",
                    headers={"Retry-After": "2"},
                )
            self._active += 1
        try:
            yield
        finally:
            async with self._lock:
                self._active -= 1


def concurrency_dependency(gate: ConcurrencyGate):
    async def dependency():
        async with gate.enter():
            yield
    return dependency


chat_limit = SlidingWindowLimit(20, 60)
upload_limit = SlidingWindowLimit(5, 60)
document_query_limit = SlidingWindowLimit(30, 60)
voice_limit = SlidingWindowLimit(20, 60)
eligibility_limit = SlidingWindowLimit(10, 60)
scheme_search_limit = SlidingWindowLimit(30, 60)
chat_gate = ConcurrencyGate(8)
upload_gate = ConcurrencyGate(2)
document_query_gate = ConcurrencyGate(12)
scheme_search_gate = ConcurrencyGate(12)
eligibility_gate = ConcurrencyGate(6)
voice_gate = ConcurrencyGate(4)
chat_capacity = concurrency_dependency(chat_gate)
upload_capacity = concurrency_dependency(upload_gate)
document_query_capacity = concurrency_dependency(document_query_gate)
scheme_search_capacity = concurrency_dependency(scheme_search_gate)
eligibility_capacity = concurrency_dependency(eligibility_gate)
voice_capacity = concurrency_dependency(voice_gate)
