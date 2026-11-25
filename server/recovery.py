"""Recovery primitives for the experimental SQLite-backed Messenger."""
from pathlib import Path
import sqlite3


def _verify_sqlite_recovery_connection(connection) -> tuple[bool, str]:
    row = connection.execute("PRAGMA integrity_check").fetchone()
    if not row or row[0] != "ok":
        return False, "STORAGE_INTEGRITY"
    return True, "STORAGE_RECOVERY_OK"


def verify_messenger_connection(connection) -> tuple[bool, str]:
    """Validate a live SQLite Messenger connection, including :memory: databases."""
    try:
        ok, code = _verify_sqlite_recovery_connection(connection)
        if not ok:
            return ok, code
        ok, code = _verify_messenger_schema_connection(connection)
        if not ok:
            return ok, code
        return _verify_messenger_data_connection(connection)
    except (sqlite3.Error, ValueError, TypeError, AttributeError):
        return False, "STORAGE_INTEGRITY"


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
    if not version_row or version_row[0] not in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"):
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
        "audio_attachments": {"object_id", "message_id", "conversation_id", "sender_ai_id", "content_type", "size", "sha256", "created_at"},
    }
    if version_row[0] in ("3", "4"):
        required_columns["voice_mutes"] = {
            "conversation_id", "ai_id", "muted_by_ai_id", "expires_at",
        }
    if version_row[0] in ("4", "5", "6", "7", "8", "9", "10"):
        required_columns["conversations"].add("kind")
        required_columns["messages"].update({"kind", "created_at_epoch_seconds"})
    if version_row[0] in ("5", "6", "7", "8", "9", "10"):
        required_columns["voice_calls"] = {
            "call_id", "conversation_id", "caller_ai_id", "callee_ai_id",
            "state", "created_at", "expires_at", "updated_at",
        }
        required_columns["voice_call_signals"] = {
            "signal_id", "call_id", "sender_ai_id", "kind", "payload_json", "created_at",
        }
    if version_row[0] in ("6", "7", "8", "9", "10"):
        required_columns["conversation_admins"] = {"conversation_id", "ai_id"}
        required_columns["room_invites"] = {
            "invite_id", "conversation_id", "token_hash", "created_by_ai_id",
            "created_at", "expires_at", "max_uses", "uses", "revoked_at",
        }
        required_columns["join_requests"] = {
            "request_id", "invite_id", "conversation_id", "ai_id", "status",
            "created_at", "decided_at", "decided_by_ai_id",
        }
    if version_row[0] in ("7", "8", "9", "10"):
        required_columns["ai_identity_directory"] = {
            "internal_number", "ai_id", "display_name", "created_at",
        }
    if version_row[0] in ("8", "9", "10"):
        required_columns["guest_applications"] = {
            "application_id", "invite_id", "conversation_id", "display_name",
            "provider_claim", "provider_verified", "status", "created_at",
            "decided_at", "decided_by_ai_id",
        }
    if version_row[0] in ("9", "10", "11"):
        required_columns["guest_applications"].update({
            "provisioning_status", "provisioned_ai_id", "provisioned_at",
        })
        required_columns["credential_records"] = {
            "token_hash", "ai_id", "status", "expires_at", "generation", "created_at",
        }
    if version_row[0] in ("10", "11"):
        required_columns["guest_applications"].update({
            "status_capability_hash", "status_capability_expires_at",
        })
    if version_row[0] == "11":
        required_columns["guest_applications"].add("status_capability_revoked_at")
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
    for row in connection.execute(
        "SELECT conversation_id, member_ai_ids FROM conversations"
    ):
        members = _parse_identifier_list(row["member_ai_ids"])
        if not row["conversation_id"] or not members:
            return False, "RESTORE_DATA_CONVERSATION_INVALID"
        conversations[row["conversation_id"]] = set(members)

    messages = {}
    for row in connection.execute(
        "SELECT message_id, conversation_id, sender_ai_id, recipient_ai_ids, "
        "client_request_id, sequence, kind, created_at_epoch_seconds FROM messages"
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
        if "kind" in row.keys() and row["kind"] not in ("NORMAL", "MISSION"):
            return False, "RESTORE_DATA_MESSAGE_INVALID"
        if "created_at_epoch_seconds" in row.keys() and (not isinstance(row["created_at_epoch_seconds"], (int, float)) or row["created_at_epoch_seconds"] < 0):
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
    if version_row and version_row[0] in ("3", "4", "5", "6", "7", "8", "9", "10"):
        for row in connection.execute(
            "SELECT conversation_id, ai_id, muted_by_ai_id, expires_at FROM voice_mutes"
        ):
            members = conversations.get(row["conversation_id"])
            if (members is None or row["ai_id"] not in members
                    or row["muted_by_ai_id"] not in members
                    or row["ai_id"] == row["muted_by_ai_id"]
                    or not isinstance(row["expires_at"], (int, float))
                    or row["expires_at"] <= 0):
                return False, "RESTORE_DATA_VOICE_MUTE_INVALID"

    if version_row and version_row[0] in ("5", "6", "7", "8", "9", "10"):
        calls = {}
        allowed_states = {"RINGING", "ACCEPTED", "CONNECTING", "CONNECTED",
                          "REJECTED", "CANCELLED", "TIMED_OUT", "ENDED", "FAILED"}
        for row in connection.execute(
            "SELECT call_id, conversation_id, caller_ai_id, callee_ai_id, state, "
            "created_at, expires_at, updated_at FROM voice_calls"
        ):
            members = conversations.get(row["conversation_id"])
            if (not row["call_id"] or row["call_id"] in calls or members is None
                    or row["caller_ai_id"] == row["callee_ai_id"]
                    or row["caller_ai_id"] not in members
                    or row["callee_ai_id"] not in members
                    or row["state"] not in allowed_states
                    or any(not isinstance(row[key], (int, float)) or row[key] <= 0
                           for key in ("created_at", "expires_at", "updated_at"))):
                return False, "RESTORE_DATA_VOICE_CALL_INVALID"
            calls[row["call_id"]] = {row["caller_ai_id"], row["callee_ai_id"]}
        for row in connection.execute(
            "SELECT call_id, sender_ai_id, kind, payload_json, created_at FROM voice_call_signals"
        ):
            try:
                payload = __import__("json").loads(row["payload_json"])
            except (TypeError, ValueError):
                return False, "RESTORE_DATA_VOICE_SIGNAL_INVALID"
            if (row["call_id"] not in calls or row["sender_ai_id"] not in calls[row["call_id"]]
                    or row["kind"] not in ("OFFER", "ANSWER", "ICE_CANDIDATE", "ICE_COMPLETE")
                    or not isinstance(payload, dict)
                    or not isinstance(row["created_at"], (int, float))
                    or row["created_at"] <= 0):
                return False, "RESTORE_DATA_VOICE_SIGNAL_INVALID"

    if version_row and version_row[0] in ("6", "7", "8", "9", "10"):
        for row in connection.execute(
            "SELECT conversation_id, ai_id FROM conversation_admins"
        ):
            if row["conversation_id"] not in conversations or row["ai_id"] not in conversations[row["conversation_id"]]:
                return False, "RESTORE_DATA_ROOM_ADMIN_INVALID"

        invites = {}
        for row in connection.execute(
            "SELECT invite_id,conversation_id,token_hash,created_by_ai_id,created_at,"
            "expires_at,max_uses,uses,revoked_at FROM room_invites"
        ):
            members = conversations.get(row["conversation_id"])
            digest = row["token_hash"]
            if (not row["invite_id"] or row["invite_id"] in invites or members is None
                    or row["created_by_ai_id"] not in members
                    or not isinstance(digest, str) or len(digest) != 64
                    or any(ch not in "0123456789abcdef" for ch in digest)
                    or not isinstance(row["created_at"], (int, float))
                    or not isinstance(row["expires_at"], (int, float))
                    or row["expires_at"] <= row["created_at"]
                    or not isinstance(row["max_uses"], int) or not 1 <= row["max_uses"] <= 20
                    or not isinstance(row["uses"], int) or not 0 <= row["uses"] <= row["max_uses"]
                    or (row["revoked_at"] is not None and not isinstance(row["revoked_at"], (int, float)))):
                return False, "RESTORE_DATA_ROOM_INVITE_INVALID"
            invites[row["invite_id"]] = (row["conversation_id"], members)

        for row in connection.execute(
            "SELECT request_id,invite_id,conversation_id,ai_id,status,created_at,"
            "decided_at,decided_by_ai_id FROM join_requests"
        ):
            invite = invites.get(row["invite_id"])
            if (not row["request_id"] or invite is None
                    or row["conversation_id"] != invite[0]
                    or row["status"] not in ("PENDING", "APPROVED", "REJECTED")
                    or not isinstance(row["created_at"], (int, float))
                    or (row["status"] == "PENDING" and
                        (row["decided_at"] is not None or row["decided_by_ai_id"] is not None))
                    or (row["status"] != "PENDING" and
                        (not isinstance(row["decided_at"], (int, float))
                         or row["decided_by_ai_id"] not in invite[1]))
                    or (row["status"] == "APPROVED" and row["ai_id"] not in conversations[row["conversation_id"]])):
                return False, "RESTORE_DATA_JOIN_REQUEST_INVALID"

    if version_row and version_row[0] in ("7", "8", "9", "10"):
        seen_numbers = set()
        seen_ai_ids = set()
        for row in connection.execute(
            "SELECT internal_number,ai_id,display_name,created_at FROM ai_identity_directory"
        ):
            if (not isinstance(row["internal_number"], int) or row["internal_number"] <= 0
                    or row["internal_number"] in seen_numbers
                    or not isinstance(row["ai_id"], str) or not row["ai_id"]
                    or row["ai_id"] in seen_ai_ids
                    or not isinstance(row["display_name"], str) or not row["display_name"].strip()
                    or len(row["display_name"]) > 80
                    or not isinstance(row["created_at"], (int, float))):
                return False, "RESTORE_DATA_IDENTITY_INVALID"
            seen_numbers.add(row["internal_number"])
            seen_ai_ids.add(row["ai_id"])

    if version_row and version_row[0] in ("8", "9", "10"):
        invites_for_guests = {row["invite_id"]: row["conversation_id"] for row in connection.execute(
            "SELECT invite_id,conversation_id FROM room_invites")}
        for row in connection.execute(
            "SELECT application_id,invite_id,conversation_id,display_name,provider_claim,"
            "provider_verified,status,created_at,decided_at,decided_by_ai_id FROM guest_applications"
        ):
            if (not row["application_id"] or row["invite_id"] not in invites_for_guests
                    or invites_for_guests[row["invite_id"]] != row["conversation_id"]
                    or not isinstance(row["display_name"], str)
                    or not row["display_name"].strip() or len(row["display_name"]) > 60
                    or row["provider_claim"] not in ("CHATGPT", "GEMINI", "CLAUDE", "KIMI", "OTHER")
                    or row["provider_verified"] != 0
                    or row["status"] not in ("PENDING", "REJECTED", "APPROVED_AWAITING_PROVISIONING")
                    or not isinstance(row["created_at"], (int, float))
                    or (row["status"] == "PENDING" and
                        (row["decided_at"] is not None or row["decided_by_ai_id"] is not None))
                    or (row["status"] != "PENDING" and
                        (not isinstance(row["decided_at"], (int, float))
                         or row["decided_by_ai_id"] not in conversations[row["conversation_id"]]))):
                return False, "RESTORE_DATA_GUEST_APPLICATION_INVALID"

    if version_row and version_row[0] in ("9", "10"):
        identities = {row["ai_id"] for row in connection.execute(
            "SELECT ai_id FROM ai_identity_directory")}
        credentials = {}
        for row in connection.execute(
            "SELECT token_hash,ai_id,status,expires_at,generation,created_at FROM credential_records"
        ):
            digest = row["token_hash"]
            if (not isinstance(digest, str) or len(digest) != 64
                    or any(ch not in "0123456789abcdef" for ch in digest)
                    or row["ai_id"] not in identities
                    or row["status"] not in ("ACTIVE", "REVOKED", "EXPIRED", "ROTATED")
                    or (row["expires_at"] is not None and
                        (not isinstance(row["expires_at"], (int, float)) or row["expires_at"] <= 0))
                    or not isinstance(row["generation"], int) or row["generation"] <= 0
                    or not isinstance(row["created_at"], (int, float)) or row["created_at"] <= 0):
                return False, "RESTORE_DATA_CREDENTIAL_INVALID"
            credentials[row["ai_id"]] = row["status"]

        for row in connection.execute(
            "SELECT application_id,conversation_id,status,provisioning_status,"
            "provisioned_ai_id,provisioned_at FROM guest_applications"
        ):
            members = conversations.get(row["conversation_id"])
            ai_id = row["provisioned_ai_id"]
            if (members is None
                    or row["provisioning_status"] not in ("NOT_STARTED", "ACTIVE", "REVOKED")):
                return False, "RESTORE_DATA_GUEST_PROVISIONING_INVALID"
            if row["provisioning_status"] == "NOT_STARTED":
                if ai_id is not None or row["provisioned_at"] is not None:
                    return False, "RESTORE_DATA_GUEST_PROVISIONING_INVALID"
            elif (not ai_id or ai_id not in identities
                  or not isinstance(row["provisioned_at"], (int, float))
                  or row["provisioned_at"] <= 0):
                return False, "RESTORE_DATA_GUEST_PROVISIONING_INVALID"
            elif row["provisioning_status"] == "ACTIVE":
                if (row["status"] != "APPROVED_AWAITING_PROVISIONING"
                        or ai_id not in members or credentials.get(ai_id) != "ACTIVE"):
                    return False, "RESTORE_DATA_GUEST_PROVISIONING_INVALID"
            elif ai_id in members or credentials.get(ai_id) != "REVOKED":
                return False, "RESTORE_DATA_GUEST_PROVISIONING_INVALID"

    if version_row and version_row[0] == "10":
        for row in connection.execute("SELECT application_id,created_at,status_capability_hash,status_capability_expires_at FROM guest_applications"):
            digest, expiry = row["status_capability_hash"], row["status_capability_expires_at"]
            if ((digest is None and expiry is not None)
                    or (digest is not None and (not isinstance(digest, str) or len(digest) != 64
                        or any(ch not in "0123456789abcdef" for ch in digest)
                        or not isinstance(expiry, (int, float)) or expiry <= row["created_at"]))):
                return False, "RESTORE_DATA_GUEST_STATUS_CAPABILITY_INVALID"
    for row in connection.execute(
        "SELECT object_id, message_id, conversation_id, sender_ai_id, content_type, size, sha256 "
        "FROM audio_attachments"
    ):
        target = messages.get(row["message_id"])
        if (
            not row["object_id"]
            or target is None
            or row["conversation_id"] != target[2]
            or row["sender_ai_id"] != target[0]
            or row["sender_ai_id"] not in target[3]
            or not isinstance(row["content_type"], str)
            or not row["content_type"]
            or not isinstance(row["size"], int)
            or row["size"] <= 0
            or not isinstance(row["sha256"], str)
            or len(row["sha256"]) != 64
            or any(ch not in "0123456789abcdef" for ch in row["sha256"].lower())
        ):
            return False, "RESTORE_DATA_AUDIO_ATTACHMENT_INVALID"
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
