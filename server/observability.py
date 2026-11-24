"""Secret-safe, bounded observability primitives for the experimental backend."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Mapping
import re


FORBIDDEN_METADATA_PARTS = (
    "token", "authorization", "credential", "secret", "password", "session",
)
_ALLOWED_OUTCOMES = {"ok", "error", "blocked"}
_MAX_EVENT_TYPES = 32


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
        if not isinstance(max_events, int) or isinstance(max_events, bool) or not 1 <= max_events <= 10000:
            raise ValueError("max_events must be between 1 and 10000")
        self._max_events = max_events
        self._events: list[OperationalEvent] = []
        self._lock = RLock()
        self._observed = 0
        self._dropped = 0
        self._outcomes = Counter()
        self._event_types = Counter()
        self._known_event_types = set()

    @staticmethod
    def _safe_metadata(metadata: Mapping[str, str]) -> dict[str, str]:
        safe: dict[str, str] = {}
        for key, value in metadata.items():
            if not isinstance(key, str):
                continue
            lowered = key.lower()
            if any(part in lowered for part in FORBIDDEN_METADATA_PARTS):
                continue
            safe[key[:64]] = str(value).replace("\\r", " ").replace("\\n", " ")[:256]
        return safe

    @staticmethod
    def _normalize_event_type(event_type: str) -> str:
        if not isinstance(event_type, str):
            return "OTHER"
        normalized = re.sub(r"[^A-Z0-9_]", "_", event_type.upper())[:64].strip("_")
        return normalized or "OTHER"

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
        normalized_type = self._normalize_event_type(event_type)
        normalized_outcome = outcome if outcome in _ALLOWED_OUTCOMES else "other"
        with self._lock:
            if normalized_type not in self._known_event_types and len(self._known_event_types) >= _MAX_EVENT_TYPES:
                normalized_type = "OTHER"
            self._known_event_types.add(normalized_type)
            event = OperationalEvent(
                event_type=normalized_type,
                timestamp=datetime.now(timezone.utc).isoformat(),
                correlation_id=correlation_id,
                principal=principal,
                outcome=normalized_outcome,
                diagnostic_code=diagnostic_code if isinstance(diagnostic_code, str) else None,
                metadata=self._safe_metadata(metadata or {}),
            )
            self._events.append(event)
            self._observed += 1
            self._outcomes[normalized_outcome] += 1
            self._event_types[normalized_type] += 1
            if len(self._events) > self._max_events:
                overflow = len(self._events) - self._max_events
                del self._events[:overflow]
                self._dropped += overflow
            return event

    def snapshot(self) -> tuple[OperationalEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def summary(self) -> dict:
        """Return aggregate counters only; never returns principals, IDs, or event payloads."""
        with self._lock:
            return {
                "eventsObserved": self._observed,
                "eventsRetained": len(self._events),
                "eventsDropped": self._dropped,
                "maxEvents": self._max_events,
                "outcomes": dict(sorted(self._outcomes.items())),
                "eventTypes": dict(sorted(self._event_types.items())),
                "storage": "PROCESS_MEMORY_ONLY",
            }
