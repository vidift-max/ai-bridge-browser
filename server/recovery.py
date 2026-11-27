"""Recovery primitives for the experimental SQLite-backed Messenger."""
from pathlib import Path
import sqlite3


def _verify_sqlite_recovery_connection(connection) -> tuple[bool, str]:
    row = connection.execute("PRAGMA integrity_check").fetchone()
    if not row or row[0] != "ok":
        return False, "STORAGE_INTEGRITY"
    return True, "STORAGE_RECOVERY_OK"


def verify_sqlite_recovery(path: str) -> tuple[bool, str]:
    """Return a safe operational result without exposing database contents."""
    db_path = Path(path)
    if not db_path.exists() or not db_path.is_file():
        return False, "STORAGE_UNAVAILABLE"
    try:
        with sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True) as connection:
            connection.execute("BEGIN")
            return _verify_sqlite_recovery_connection(connection)
    except (OSError, sqlite3.Error):
        return False, "STORAGE_INTEGRITY"


def _verify_messenger_schema_connection(connection) -> tuple[bool, str]:
    version_row = connection.execute(
        "SELECT value FROM schema_meta WHERE key='version'"
    ).fetchone()
    if not version_row or version_row[0] not in ("1", "2", "3"):
        return False, "RESTORE_SCHEMA_UNSUPPORTED"
    schema_version = version_row[0]
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
        if not expected.issubset({row[1] for row in rows}):
            return False, "RESTORE_SCHEMA_UNSUPPORTED"
    index_row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' "
        "AND name='idx_messages_conversation_sequence'"
    ).fetchone()
    if not index_row or not index_row[0] or "CREATE UNIQUE INDEX" not in index_row[0].upper():
        return False, "RESTORE_SCHEMA_UNSUPPORTED"
    index_columns = [row[2] for row in connection.execute(
        "PRAGMA index_info(idx_messages_conversation_sequence)"
    )]
    if index_columns != ["conversation_id", "sequence"]:
        return False, "RESTORE_SCHEMA_UNSUPPORTED"
    if schema_version in ("2", "3"):
        invitation_columns = {
            "invitation_id", "conversation_id", "target_ai_id", "token_hash",
            "status", "created_by_ai_id", "created_at", "expires_at",
            "accepted_at", "revoked_at",
        }
        rows = connection.execute("PRAGMA table_info(invitations)").fetchall()
        if not invitation_columns.issubset({row[1] for row in rows}):
            return False, "RESTORE_SCHEMA_UNSUPPORTED"
        indexes = {row[1] for row in connection.execute("PRAGMA index_list(invitations)")}
        if not {"sqlite_autoindex_invitations_2", "idx_invitations_conversation_status",
                "idx_invitations_target_status"}.issubset(indexes):
            return False, "RESTORE_SCHEMA_UNSUPPORTED"
    if schema_version == "3":
        conversation_columns = {row[1] for row in connection.execute("PRAGMA table_info(conversations)")}
        if "conversation_kind" not in conversation_columns:
            return False, "RESTORE_SCHEMA_UNSUPPORTED"
    return True, "RESTORE_SCHEMA_COMPATIBLE"


def verify_messenger_schema(path: str) -> tuple[bool, str]:
    """Inspect the Messenger schema in read-only mode; never migrate or mutate it."""
    db_path = Path(path)
    if not db_path.is_file():
        return False, "RESTORE_SCHEMA_UNAVAILABLE"
    try:
        with sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True) as connection:
            connection.execute("BEGIN")
            return _verify_messenger_schema_connection(connection)
    except (OSError, sqlite3.Error, ValueError):
        return False, "RESTORE_SCHEMA_UNSUPPORTED"


def _parse_identifier_list(value, *, allow_empty: bool = False):
    """Parse comma-delimited IDs without silently dropping malformed entries."""
    if not isinstance(value, str):
        return None
    if value == "" and allow_empty:
        return []
    parts = value.split(",")
    if any(not item or item != item.strip() for item in parts):
        return None
    if len(parts) != len(set(parts)):
        return None
    return parts


def _verify_messenger_data_connection(connection) -> tuple[bool, str]:
    connection.row_factory = sqlite3.Row
    conversations = {}
    version_row = connection.execute(
        "SELECT value FROM schema_meta WHERE key='version'"
    ).fetchone()
    schema_version = version_row[0] if version_row else None
    conversation_query = ("SELECT conversation_id, member_ai_ids, conversation_kind FROM conversations"
                          if schema_version == "3"
                          else "SELECT conversation_id, member_ai_ids FROM conversations")
    for row in connection.execute(conversation_query):
        members = _parse_identifier_list(row["member_ai_ids"])
        if not row["conversation_id"] or not members:
            return False, "RESTORE_DATA_CONVERSATION_INVALID"
        if schema_version == "3":
            kind = row["conversation_kind"]
            if (kind not in ("PRIVATE", "GROUP") or len(members) < 2
                    or (kind == "PRIVATE" and len(members) != 2)
                    or (kind == "GROUP" and len(members) > 20)):
                return False, "RESTORE_DATA_CONVERSATION_INVALID"
        conversations[row["conversation_id"]] = set(members)

    messages = {}
    for row in connection.execute(
        "SELECT message_id, conversation_id, sender_ai_id, recipient_ai_ids, "
        "client_request_id, sequence FROM messages"
    ):
        message_id = row["message_id"]
        members = conversations.get(row["conversation_id"])
        recipients = _parse_identifier_list(row["recipient_ai_ids"], allow_empty=True)
        if (not message_id or message_id in messages or members is None or recipients is None
                or not row["sender_ai_id"] or row["sender_ai_id"] not in members
                or not row["client_request_id"] or not isinstance(row["sequence"], int)
                or row["sequence"] <= 0
                or len(recipients) != len(set(recipients))
                or any(item not in members for item in recipients)):
            return False, "RESTORE_DATA_MESSAGE_INVALID"
        messages[message_id] = (row["sender_ai_id"], row["client_request_id"],
                                row["conversation_id"], members, set(recipients))

    idempotency_keys = set()
    for row in connection.execute(
        "SELECT sender_ai_id, client_request_id, message_id FROM idempotency"
    ):
        target = messages.get(row["message_id"])
        key = (row["sender_ai_id"], row["client_request_id"])
        if (target is None or target[0] != row["sender_ai_id"]
                or target[1] != row["client_request_id"] or key in idempotency_keys):
            return False, "RESTORE_DATA_IDEMPOTENCY_INVALID"
        idempotency_keys.add(key)
    expected_idempotency = {(sender, request_id) for sender, request_id, _, _, _ in messages.values()}
    if idempotency_keys != expected_idempotency:
        return False, "RESTORE_DATA_IDEMPOTENCY_INVALID"

    for row in connection.execute("SELECT message_id, ai_id FROM acknowledgements"):
        target = messages.get(row["message_id"])
        if target is None or row["ai_id"] not in target[4]:
            return False, "RESTORE_DATA_ACKNOWLEDGEMENT_INVALID"
    version_row = connection.execute(
        "SELECT value FROM schema_meta WHERE key='version'"
    ).fetchone()
    if version_row and version_row[0] in ("2", "3"):
        import re
        for row in connection.execute(
            "SELECT invitation_id, conversation_id, target_ai_id, token_hash, status, "
            "created_by_ai_id, created_at, expires_at, accepted_at, revoked_at FROM invitations"
        ):
            members = conversations.get(row["conversation_id"])
            if (not row["invitation_id"] or not row["target_ai_id"] or members is None
                    or row["created_by_ai_id"] not in members
                    or not isinstance(row["token_hash"], str)
                    or re.fullmatch(r"[0-9a-f]{64}", row["token_hash"]) is None
                    or row["status"] not in ("PENDING", "ACCEPTED", "REVOKED", "EXPIRED")
                    or not isinstance(row["created_at"], int) or row["created_at"] < 0
                    or not isinstance(row["expires_at"], int) or row["expires_at"] <= row["created_at"]):
                return False, "RESTORE_DATA_INVITATION_INVALID"
            accepted = row["accepted_at"] is not None
            revoked = row["revoked_at"] is not None
            if ((row["status"] == "ACCEPTED" and (not accepted or revoked or row["target_ai_id"] not in members))
                    or (row["status"] == "REVOKED" and (not revoked or accepted))
                    or (row["status"] in ("PENDING", "EXPIRED") and (accepted or revoked))):
                return False, "RESTORE_DATA_INVITATION_INVALID"
    return True, "RESTORE_DATA_CONSISTENT"


def verify_messenger_data_consistency(path: str) -> tuple[bool, str]:
    """Check persisted Messenger references in read-only mode; never repair data."""
    db_path = Path(path)
    if not db_path.is_file():
        return False, "RESTORE_DATA_UNAVAILABLE"
    try:
        with sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True) as connection:
            connection.execute("BEGIN")
            return _verify_messenger_data_connection(connection)
    except (OSError, sqlite3.Error, ValueError, TypeError, AttributeError):
        return False, "RESTORE_DATA_UNREADABLE"
