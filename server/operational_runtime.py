"""Small integration boundary for experimental Messenger operations."""
from server.observability import OperationalEventLog
from server.recovery import verify_sqlite_recovery


class OperationalRuntime:
    def __init__(self, max_events: int = 1000):
        self.events = OperationalEventLog(max_events=max_events)

    def record(self, event_type: str, *, correlation_id=None, principal=None,
               outcome="ok", diagnostic_code=None, metadata=None):
        return self.events.record(
            event_type,
            correlation_id=correlation_id,
            principal=principal,
            outcome=outcome,
            diagnostic_code=diagnostic_code,
            metadata=metadata,
        )

    def check_storage(self, path: str, *, correlation_id=None):
        ok, code = verify_sqlite_recovery(path)
        self.record(
            "STORAGE_RECOVERY_CHECK",
            correlation_id=correlation_id,
            outcome="ok" if ok else "error",
            diagnostic_code=None if ok else code,
        )
        return ok, code

    def snapshot(self):
        return self.events.snapshot()
