"""Secret-safe, bounded observability primitives for the experimental backend."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


FORBIDDEN_METADATA_PARTS = (
    "token",
    "authorization",
    "credential",
    "secret",
    "password",
    "session",
)


@dataclass(frozen=True)
class OperationalEvent:
    event_type: str
    timestamp: str
    correlation_id: str | None
    principal: str | None
    outcome: str
    diagnostic_code: str | None
    metadata: Mapping[str, str]


class OperationalEventLog:
    """Bounded in-memory event log; deliberately not a production telemetry sink."""

    def __init__(self, max_events: int = 1000):
        if not isinstance(max_events, int) or not 1 <= max_events <= 10000:
            raise ValueError("max_events must be between 1 and 10000")
        self._max_events = max_events
        self._events: list[OperationalEvent] = []

    @staticmethod
    def _safe_metadata(metadata: Mapping[str, str]) -> dict[str, str]:
        safe: dict[str, str] = {}
        for key, value in metadata.items():
            lowered = key.lower()
            if any(part in lowered for part in FORBIDDEN_METADATA_PARTS):
                continue
            safe[key] = str(value)[:256]
        return safe

    def record(
        self,
        event_type: str,
        *,
        correlation_id: str | None = None,
        principal: str | None = None,
        outcome: str = "ok",
        diagnostic_code: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> OperationalEvent:
        event = OperationalEvent(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            correlation_id=correlation_id,
            principal=principal,
            outcome=outcome,
            diagnostic_code=diagnostic_code,
            metadata=self._safe_metadata(metadata or {}),
        )
        self._events.append(event)
        if len(self._events) > self._max_events:
            del self._events[0 : len(self._events) - self._max_events]
        return event

    def snapshot(self) -> tuple[OperationalEvent, ...]:
        return tuple(self._events)
