from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Dict, List, Optional
from uuid import uuid4


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    correlation_id: str
    event_type: str
    ai_id: Optional[str]
    subject: str
    timestamp: datetime
    metadata: Dict[str, str]


class AuditEventType:
    AUTHENTICATED = "AUTHENTICATED"
    CREDENTIAL_REVOKED = "CREDENTIAL_REVOKED"
    CREDENTIAL_EXPIRED = "CREDENTIAL_EXPIRED"
    CREDENTIAL_ROTATED = "CREDENTIAL_ROTATED"
    MESSAGE_SUBMITTED = "MESSAGE_SUBMITTED"
    MESSAGE_READ = "MESSAGE_READ"
    MESSAGE_ACKNOWLEDGED = "MESSAGE_ACKNOWLEDGED"


class AuditLog:
    """Experimental in-memory audit sink; bearer/session secrets are rejected."""

    _SECRET_KEYS = {"token", "bearer", "authorization", "session_token", "credential", "password"}

    def __init__(self):
        self._events: List[AuditEvent] = []
        self._lock = RLock()

    def record(self, event_type: str, subject: str, ai_id: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               now: Optional[datetime] = None,
               correlation_id: Optional[str] = None) -> AuditEvent:
        safe_metadata = {}
        safe_subject = str(subject)
        lowered_subject = safe_subject.lower()
        if "token" in lowered_subject or "authorization" in lowered_subject or "bearer" in lowered_subject:
            safe_subject = "[redacted]"
        for key, value in dict(metadata or {}).items():
            if key.lower() in self._SECRET_KEYS or "token" in key.lower() or "authorization" in key.lower():
                continue
            safe_metadata[key] = value
        with self._lock:
            event = AuditEvent(
                event_id=str(uuid4()),
                correlation_id=correlation_id or str(uuid4()),
                event_type=event_type,
                ai_id=ai_id,
                subject=safe_subject,
                timestamp=now or datetime.now(timezone.utc),
                metadata=safe_metadata,
            )
            self._events.append(event)
        return event

    def events(self) -> List[AuditEvent]:
        with self._lock:
            return list(self._events)
