"""Recovery primitives for the experimental SQLite-backed Messenger."""

from pathlib import Path
import sqlite3


def verify_sqlite_recovery(path: str) -> tuple[bool, str]:
    """Return a safe operational result without exposing database contents."""
    db_path = Path(path)
    if not db_path.exists():
        return False, "STORAGE_UNAVAILABLE"
    if not db_path.is_file():
        return False, "STORAGE_UNAVAILABLE"
    try:
        with sqlite3.connect(str(db_path)) as connection:
            row = connection.execute("PRAGMA integrity_check").fetchone()
    except (OSError, sqlite3.Error):
        return False, "STORAGE_INTEGRITY"
    if not row or row[0] != "ok":
        return False, "STORAGE_INTEGRITY"
    return True, "STORAGE_RECOVERY_OK"

def verify_messenger_schema(path: str) -> tuple[bool, str]:
    """Inspect the Messenger schema in read-only mode; never migrate or mutate it."""
    db_path = Path(path)
    if not db_path.is_file():
        return False, "RESTORE_SCHEMA_UNAVAILABLE"
    try:
        with sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True) as connection:
            version_row = connection.execute(
                "SELECT value FROM schema_meta WHERE key='version'"
            ).fetchone()
            if not version_row or version_row[0] != "1":
                return False, "RESTORE_SCHEMA_UNSUPPORTED"
            required_columns = {
                "schema_meta": {"key", "value"},
                "conversations": {"conversation_id", "member_ai_ids"},
                "messages": {
                    "message_id", "conversation_id", "sender_ai_id",
                    "recipient_ai_ids", "body", "client_request_id", "sequence",
                },
                "idempotency": {"sender_ai_id", "client_request_id", "message_id"},
                "acknowledgements": {"message_id", "ai_id"},
            }
            for table, expected in required_columns.items():
                rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
                actual = {row[1] for row in rows}
                if not expected.issubset(actual):
                    return False, "RESTORE_SCHEMA_UNSUPPORTED"
            index_row = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='index' "
                "AND name='idx_messages_conversation_sequence'"
            ).fetchone()
            if not index_row:
                return False, "RESTORE_SCHEMA_UNSUPPORTED"
    except (OSError, sqlite3.Error, ValueError):
        return False, "RESTORE_SCHEMA_UNSUPPORTED"
    return True, "RESTORE_SCHEMA_COMPATIBLE"

