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
        with sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True) as connection:
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

def verify_messenger_data_consistency(path: str) -> tuple[bool, str]:
    """Check persisted Messenger references in read-only mode; never repair data."""
    db_path = Path(path)
    if not db_path.is_file():
        return False, "RESTORE_DATA_UNAVAILABLE"
    try:
        with sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            conversations = {}
            for row in connection.execute(
                "SELECT conversation_id, member_ai_ids FROM conversations"
            ):
                members = [item for item in row["member_ai_ids"].split(",") if item]
                if not row["conversation_id"] or len(members) != len(set(members)):
                    return False, "RESTORE_DATA_CONVERSATION_INVALID"
                conversations[row["conversation_id"]] = set(members)

            messages = {}
            for row in connection.execute(
                "SELECT message_id, conversation_id, sender_ai_id, recipient_ai_ids, "
                "client_request_id, sequence FROM messages"
            ):
                message_id = row["message_id"]
                members = conversations.get(row["conversation_id"])
                recipients = [item for item in row["recipient_ai_ids"].split(",") if item]
                if (not message_id or message_id in messages or members is None
                        or not row["sender_ai_id"] or row["sender_ai_id"] not in members
                        or not row["client_request_id"] or not isinstance(row["sequence"], int)
                        or row["sequence"] <= 0
                        or len(recipients) != len(set(recipients))
                        or any(item not in members for item in recipients)):
                    return False, "RESTORE_DATA_MESSAGE_INVALID"
                messages[message_id] = (row["sender_ai_id"], row["client_request_id"],
                                         row["conversation_id"], members)

            for row in connection.execute(
                "SELECT sender_ai_id, client_request_id, message_id FROM idempotency"
            ):
                target = messages.get(row["message_id"])
                if (target is None or target[0] != row["sender_ai_id"]
                        or target[1] != row["client_request_id"]):
                    return False, "RESTORE_DATA_IDEMPOTENCY_INVALID"

            for row in connection.execute(
                "SELECT message_id, ai_id FROM acknowledgements"
            ):
                target = messages.get(row["message_id"])
                if target is None or row["ai_id"] not in target[3]:
                    return False, "RESTORE_DATA_ACKNOWLEDGEMENT_INVALID"
    except (OSError, sqlite3.Error, ValueError, TypeError):
        return False, "RESTORE_DATA_UNREADABLE"
    return True, "RESTORE_DATA_CONSISTENT"
