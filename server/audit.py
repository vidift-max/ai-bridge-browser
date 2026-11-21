from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    ai_id: Optional[str]
    subject: str
    timestamp: datetime
    metadata: Dict[str, str]


class AuditLog:
    """Experimental in-memory audit sink; secrets are never recorded."""

    def __init__(self):
        self._events: List[AuditEvent] = []

    def record(self, event_type: str, subject: str, ai_id: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               now: Optional[datetime] = None) -> AuditEvent:
        event = AuditEvent(
            event_type=event_type,
            ai_id=ai_id,
            subject=subject,
            timestamp=now or datetime.now(timezone.utc),
            metadata=dict(metadata or {}),
        )
        self._events.append(event)
        return event

    def events(self) -> List[AuditEvent]:
        return list(self._events)
