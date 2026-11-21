from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict, Optional


class RateLimitExceeded(PermissionError):
    pass


class SlidingWindowRateLimiter:
    """Experimental per-principal limiter; state is intentionally runtime-only."""

    def __init__(self, max_events: int = 60, window_seconds: int = 60):
        if max_events < 1 or window_seconds < 1:
            raise ValueError("rate_limit_configuration_invalid")
        self.max_events = max_events
        self.window = timedelta(seconds=window_seconds)
        self._events: Dict[str, Deque[datetime]] = defaultdict(deque)

    def allow(self, principal: str, now: Optional[datetime] = None) -> bool:
        if not principal:
            raise ValueError("principal_required")
        current = now or datetime.now(timezone.utc)
        events = self._events[principal]
        cutoff = current - self.window
        while events and events[0] <= cutoff:
            events.popleft()
        if len(events) >= self.max_events:
            raise RateLimitExceeded("rate_limit_exceeded")
        events.append(current)
        return True
