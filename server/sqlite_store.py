import sqlite3
import json
import time
import hmac
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCHEMA_VERSION = 13

class SQLiteMessengerStore:
    """Small stdlib-only durable store for the experimental Messenger backend."""

    def __init__(self, path: str):
        if not path:
            raise ValueError("storage_path_required")
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._migrate()

    @property
    def connection(self):
        """Expose the live connection for read-only operational integrity checks."""
        return self._connection

    def _migrate(self):
        self._connection.execute("CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        row = self._connection.execute("SELECT value FROM schema_meta WHERE key='version'").fetchone()
        version = int(row["value"]) if row else 0
        if version > SCHEMA_VERSION:
            raise RuntimeError("unsupported_schema_version")
        if version < 1:
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    member_ai_ids TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    sender_ai_id TEXT NOT NULL,
                    recipient_ai_ids TEXT NOT NULL,
                    body TEXT NOT NULL,
                    client_request_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS idempotency (
                    sender_ai_id TEXT NOT NULL,
                    client_request_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    PRIMARY KEY(sender_ai_id, client_request_id)
                );
                CREATE TABLE IF NOT EXISTS acknowledgements (
                    message_id TEXT NOT NULL,
                    ai_id TEXT NOT NULL,
                    PRIMARY KEY(message_id, ai_id)
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_conversation_sequence
                    ON messages(conversation_id, sequence);
            """)
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','1')")
            self._connection.commit()
            version = 1
        if version < 2:
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS audio_attachments (
                    object_id TEXT PRIMARY KEY,
                    message_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    sender_ai_id TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(message_id, object_id)
                );
                CREATE INDEX IF NOT EXISTS idx_audio_attachments_message
                    ON audio_attachments(message_id);
            """)
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','2')")
            self._connection.commit()
        if version < 3:
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS voice_mutes (
                    conversation_id TEXT NOT NULL,
                    ai_id TEXT NOT NULL,
                    muted_by_ai_id TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    PRIMARY KEY(conversation_id, ai_id)
                );
                CREATE INDEX IF NOT EXISTS idx_voice_mutes_expiry
                    ON voice_mutes(expires_at);
            """)
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','3')")
            self._connection.commit()

        if version < 4:
            self._connection.executescript("""
                ALTER TABLE conversations ADD COLUMN kind TEXT NOT NULL DEFAULT 'GROUP';
                ALTER TABLE messages ADD COLUMN kind TEXT NOT NULL DEFAULT 'NORMAL';
                ALTER TABLE messages ADD COLUMN created_at_epoch_seconds REAL NOT NULL DEFAULT 0;
            """)
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','4')")
            self._connection.commit()
            version = 4

        if version < 5:
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS voice_calls (
                    call_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    caller_ai_id TEXT NOT NULL,
                    callee_ai_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_voice_calls_conversation_state
                    ON voice_calls(conversation_id,state);
                CREATE TABLE IF NOT EXISTS voice_call_signals (
                    signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_id TEXT NOT NULL,
                    sender_ai_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_voice_call_signals_call
                    ON voice_call_signals(call_id,signal_id);
            """)
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','5')")
            self._connection.commit()
            version = 5

        if version < 6:
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS conversation_admins (
                    conversation_id TEXT NOT NULL,
                    ai_id TEXT NOT NULL,
                    PRIMARY KEY(conversation_id, ai_id)
                );
                CREATE TABLE IF NOT EXISTS room_invites (
                    invite_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_by_ai_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    max_uses INTEGER NOT NULL,
                    uses INTEGER NOT NULL DEFAULT 0,
                    revoked_at REAL
                );
                CREATE INDEX IF NOT EXISTS idx_room_invites_conversation
                    ON room_invites(conversation_id, created_at);
                CREATE TABLE IF NOT EXISTS join_requests (
                    request_id TEXT PRIMARY KEY,
                    invite_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    ai_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    decided_at REAL,
                    decided_by_ai_id TEXT,
                    UNIQUE(invite_id, ai_id)
                );
                CREATE INDEX IF NOT EXISTS idx_join_requests_room_status
                    ON join_requests(conversation_id, status, created_at);
            """)
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','6')")
            self._connection.commit()
            version = 6

        if version < 7:
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS ai_identity_directory (
                    internal_number INTEGER PRIMARY KEY AUTOINCREMENT,
                    ai_id TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    created_at REAL NOT NULL DEFAULT (unixepoch())
                );
            """)
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','7')")
            self._connection.commit()
            version = 7



        if version < 8:
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS guest_applications (
                    application_id TEXT PRIMARY KEY,
                    invite_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    provider_claim TEXT NOT NULL,
                    provider_verified INTEGER NOT NULL DEFAULT 0 CHECK(provider_verified=0),
                    status TEXT NOT NULL CHECK(status IN ('PENDING','REJECTED','APPROVED_AWAITING_PROVISIONING')),
                    created_at REAL NOT NULL,
                    decided_at REAL,
                    decided_by_ai_id TEXT,
                    UNIQUE(invite_id, display_name)
                );
                CREATE INDEX IF NOT EXISTS idx_guest_applications_room_status
                    ON guest_applications(conversation_id,status,created_at);
            """)
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','8')")
            self._connection.commit()
            version = 8

        if version < 9:
            self._connection.executescript("""
                ALTER TABLE guest_applications
                    ADD COLUMN provisioning_status TEXT NOT NULL DEFAULT 'NOT_STARTED'
                    CHECK(provisioning_status IN ('NOT_STARTED','ACTIVE','REVOKED'));
                ALTER TABLE guest_applications ADD COLUMN provisioned_ai_id TEXT;
                ALTER TABLE guest_applications ADD COLUMN provisioned_at REAL;
                CREATE UNIQUE INDEX IF NOT EXISTS idx_guest_application_provisioned_ai
                    ON guest_applications(provisioned_ai_id)
                    WHERE provisioned_ai_id IS NOT NULL;
                CREATE TABLE IF NOT EXISTS credential_records (
                    token_hash TEXT PRIMARY KEY,
                    ai_id TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('ACTIVE','REVOKED','EXPIRED','ROTATED')),
                    expires_at REAL,
                    generation INTEGER NOT NULL DEFAULT 1,
                    created_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_credential_records_ai
                    ON credential_records(ai_id,status);
            """)
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','9')")
            self._connection.commit()
            version = 9



        if version < 10:
            self._connection.executescript("""
                ALTER TABLE guest_applications ADD COLUMN status_capability_hash TEXT;
                ALTER TABLE guest_applications ADD COLUMN status_capability_expires_at REAL;
                CREATE UNIQUE INDEX IF NOT EXISTS idx_guest_application_status_capability
                    ON guest_applications(status_capability_hash)
                    WHERE status_capability_hash IS NOT NULL;
            """)
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','10')")
            self._connection.commit()
            version = 10

        if version < 11:
            self._connection.execute(
                "ALTER TABLE guest_applications ADD COLUMN status_capability_revoked_at REAL")
            self._connection.execute(
                "INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','11')")
            self._connection.commit()
            version = 11

        if version < 12:
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS provider_request_records (
                    principal_ai_id TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    request_digest TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('PROCESSING','COMPLETED','FAILED')),
                    conversation_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    response_text TEXT,
                    provider_id TEXT,
                    model TEXT,
                    attestation_json TEXT,
                    message_id TEXT,
                    error_code TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY(principal_ai_id, request_id)
                );
                CREATE INDEX IF NOT EXISTS idx_provider_request_message
                    ON provider_request_records(message_id);
            """)
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','12')")
            self._connection.commit()
            version = 12

        if version < 13:
            self._connection.execute(
                "ALTER TABLE provider_request_records ADD COLUMN attempt_generation INTEGER NOT NULL DEFAULT 1")
            self._connection.execute("CREATE INDEX IF NOT EXISTS idx_provider_request_processing "
                                     "ON provider_request_records(status,updated_at)")
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','13')")
            self._connection.commit()
            version = 13

    def create_guest_application(self, application, token_hash, status_capability_hash=None, status_capability_expires_at=None):
        """Atomically persist an application and optional digest-only status capability."""
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            invite = self._connection.execute("SELECT * FROM room_invites WHERE token_hash=?", (token_hash,)).fetchone()
            now = application["created_at"]
            if invite is None:
                self._connection.rollback()
                return None, "invite_unavailable"
            # A capability-bound retry may recover its own receipt after invite expiry
            # or revocation; it must never create a new application in that state.
            existing = self._connection.execute("SELECT * FROM guest_applications WHERE invite_id=? AND display_name=?", (invite["invite_id"], application["display_name"])).fetchone()
            if existing is not None:
                stored, supplied = existing["status_capability_hash"], status_capability_hash
                replay = bool(stored and supplied and existing["status_capability_expires_at"] is not None and existing["status_capability_expires_at"] > now and hmac.compare_digest(stored, supplied))
                self._connection.rollback()
                return dict(existing), "request_replay" if replay else "request_exists"
            if invite["revoked_at"] is not None or invite["expires_at"] <= now:
                self._connection.rollback()
                return None, "invite_unavailable"
            if status_capability_hash:
                capability_owner = self._connection.execute("SELECT application_id FROM guest_applications WHERE status_capability_hash=?", (status_capability_hash,)).fetchone()
                if capability_owner is not None:
                    self._connection.rollback()
                    return None, "request_exists"
            if invite["uses"] >= invite["max_uses"]:
                self._connection.rollback()
                return None, "invite_unavailable"
            self._connection.execute("""INSERT INTO guest_applications(application_id,invite_id,conversation_id,display_name,provider_claim,provider_verified,status,created_at,status_capability_hash,status_capability_expires_at) VALUES(?,?,?,?,?,0,'PENDING',?,?,?)""", (application["application_id"], invite["invite_id"], invite["conversation_id"], application["display_name"], application["provider_claim"], now, status_capability_hash, status_capability_expires_at))
            self._connection.execute("UPDATE room_invites SET uses=uses+1 WHERE invite_id=?", (invite["invite_id"],))
            row = self._connection.execute("SELECT * FROM guest_applications WHERE application_id=?", (application["application_id"],)).fetchone()
            self._connection.commit()
            return dict(row), "created"
        except Exception:
            self._connection.rollback()
            raise

    def get_guest_application_status(self, status_capability_hash, now):
        """Return only public lifecycle state for a valid, unexpired capability."""
        row = self._connection.execute("""SELECT status,provisioning_status,created_at,decided_at,provisioned_at,status_capability_expires_at,status_capability_revoked_at FROM guest_applications WHERE status_capability_hash=?""", (status_capability_hash,)).fetchone()
        if row is None or row["status_capability_expires_at"] is None or row["status_capability_expires_at"] <= now:
            return None
        if row["provisioning_status"] == "REVOKED": state = "REVOKED"
        elif row["provisioning_status"] == "ACTIVE": state = "ACTIVE"
        else: state = row["status"]
        updated = max(v for v in (row["created_at"], row["decided_at"], row["provisioned_at"], row["status_capability_revoked_at"]) if v is not None)
        return {"state": state, "updatedAt": updated}

    def provision_guest_application(self, conversation_id, application_id, ai_id, display_name,
                                     token_hash, expires_at, provisioned_at):
        """Atomically add one approved guest identity, room membership and credential digest."""
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            app = self._connection.execute(
                """SELECT * FROM guest_applications WHERE application_id=?""",
                (application_id,)).fetchone()
            if (app is None or app["conversation_id"] != conversation_id
                    or app["status"] != "APPROVED_AWAITING_PROVISIONING"
                    or app["provisioning_status"] != "NOT_STARTED"):
                self._connection.rollback()
                return None
            conversation = self._connection.execute(
                "SELECT member_ai_ids FROM conversations WHERE conversation_id=?",
                (app["conversation_id"],)).fetchone()
            if conversation is None:
                self._connection.rollback()
                return None
            members = set(filter(None, conversation["member_ai_ids"].split(",")))
            if ai_id in members or len(members) >= 20:
                self._connection.rollback()
                return None
            self._connection.execute(
                "INSERT INTO ai_identity_directory(ai_id,display_name,created_at) VALUES(?,?,?)",
                (ai_id, app["display_name"], provisioned_at))
            members.add(ai_id)
            self._connection.execute(
                "UPDATE conversations SET member_ai_ids=? WHERE conversation_id=?",
                (",".join(sorted(members)), app["conversation_id"]))
            self._connection.execute(
                """INSERT INTO credential_records(token_hash,ai_id,status,expires_at,generation,created_at)
                   VALUES(?,?,'ACTIVE',?,1,?)""",
                (token_hash, ai_id, expires_at, provisioned_at))
            cursor = self._connection.execute(
                """UPDATE guest_applications
                   SET provisioning_status='ACTIVE',provisioned_ai_id=?,provisioned_at=?
                   WHERE application_id=? AND provisioning_status='NOT_STARTED'
                     AND status='APPROVED_AWAITING_PROVISIONING'""",
                (ai_id, provisioned_at, application_id))
            if cursor.rowcount != 1:
                self._connection.rollback()
                return None
            self._connection.commit()
            return {"application_id": application_id, "conversation_id": app["conversation_id"],
                    "ai_id": ai_id, "display_name": app["display_name"],
                    "provider_claim": app["provider_claim"], "provisioned_at": provisioned_at}
        except Exception:
            self._connection.rollback()
            raise



    def revoke_guest_provisioning(self, conversation_id, application_id, revoked_at):
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            app = self._connection.execute(
                """SELECT provisioned_ai_id,provisioning_status FROM guest_applications
                   WHERE application_id=? AND conversation_id=?""",
                (application_id, conversation_id)).fetchone()
            if app is None or app["provisioning_status"] != "ACTIVE" or not app["provisioned_ai_id"]:
                self._connection.rollback()
                return None
            ai_id = app["provisioned_ai_id"]
            room = self._connection.execute(
                "SELECT member_ai_ids FROM conversations WHERE conversation_id=?",
                (conversation_id,)).fetchone()
            members = set(filter(None, room["member_ai_ids"].split(","))) if room else set()
            members.discard(ai_id)
            self._connection.execute(
                "UPDATE conversations SET member_ai_ids=? WHERE conversation_id=?",
                (",".join(sorted(members)), conversation_id))
            credential = self._connection.execute(
                "SELECT token_hash FROM credential_records WHERE ai_id=? AND status='ACTIVE'",
                (ai_id,)).fetchone()
            self._connection.execute(
                "UPDATE credential_records SET status='REVOKED' WHERE ai_id=? AND status='ACTIVE'",
                (ai_id,))
            self._connection.execute(
                """UPDATE guest_applications
                   SET provisioning_status='REVOKED',status_capability_revoked_at=?
                   WHERE application_id=? AND conversation_id=? AND provisioning_status='ACTIVE'""",
                (revoked_at, application_id, conversation_id))
            self._connection.commit()
            return {"ai_id": ai_id, "conversation_id": conversation_id, "token_hash": credential["token_hash"] if credential else None}
        except Exception:
            self._connection.rollback()
            raise


    def list_guest_applications(self, conversation_id):
        rows = self._connection.execute(
            """SELECT application_id,conversation_id,display_name,provider_claim,
               provider_verified,status,created_at,decided_at,decided_by_ai_id,
               provisioning_status,provisioned_ai_id,provisioned_at
               FROM guest_applications WHERE conversation_id=?
               ORDER BY created_at,application_id""", (conversation_id,)).fetchall()
        return [dict(row) for row in rows]

    def decide_guest_application(self, conversation_id, application_id, decision,
                                 decided_by_ai_id, decided_at):
        status = ("APPROVED_AWAITING_PROVISIONING" if decision == "APPROVE" else "REJECTED")
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            cursor = self._connection.execute(
                """UPDATE guest_applications SET status=?,decided_at=?,decided_by_ai_id=?
                   WHERE application_id=? AND conversation_id=? AND status='PENDING'""",
                (status, decided_at, decided_by_ai_id, application_id, conversation_id))
            if cursor.rowcount != 1:
                self._connection.rollback()
                return None
            row = self._connection.execute(
                "SELECT application_id,conversation_id,display_name,provider_claim,"
                "provider_verified,status,created_at,decided_at,decided_by_ai_id "
                "FROM guest_applications WHERE application_id=?",
                (application_id,)).fetchone()
            self._connection.commit()
            return dict(row)
        except Exception:
            self._connection.rollback()
            raise


    def save_voice_mute(self, conversation_id: str, ai_id: str,
                        muted_by_ai_id: str, expires_at: float):
        self._connection.execute(
            """INSERT INTO voice_mutes(conversation_id,ai_id,muted_by_ai_id,expires_at)
               VALUES(?,?,?,?)
               ON CONFLICT(conversation_id,ai_id) DO UPDATE SET
                 muted_by_ai_id=excluded.muted_by_ai_id,
                 expires_at=excluded.expires_at""",
            (conversation_id, ai_id, muted_by_ai_id, expires_at),
        )
        self._connection.commit()

    def delete_voice_mute(self, conversation_id: str, ai_id: str) -> bool:
        cursor = self._connection.execute(
            "DELETE FROM voice_mutes WHERE conversation_id=? AND ai_id=?",
            (conversation_id, ai_id))
        self._connection.commit()
        return cursor.rowcount == 1

    def load_active_voice_mutes(self, now: float):
        self._connection.execute("DELETE FROM voice_mutes WHERE expires_at<=?", (now,))
        self._connection.commit()
        return self._connection.execute(
            """SELECT conversation_id,ai_id,muted_by_ai_id,expires_at
               FROM voice_mutes WHERE expires_at>?""", (now,)).fetchall()

    def save_voice_call(self, call):
        self._connection.execute(
            """INSERT INTO voice_calls(call_id,conversation_id,caller_ai_id,callee_ai_id,
               state,created_at,expires_at,updated_at) VALUES(?,?,?,?,?,?,?,?)""",
            tuple(call[key] for key in ("call_id","conversation_id","caller_ai_id",
                "callee_ai_id","state","created_at","expires_at","updated_at")))
        self._connection.commit()

    def update_voice_call(self, call):
        cursor = self._connection.execute(
            """UPDATE voice_calls SET state=?,expires_at=?,updated_at=? WHERE call_id=?""",
            (call["state"],call["expires_at"],call["updated_at"],call["call_id"]))
        self._connection.commit()
        if cursor.rowcount != 1:
            raise ValueError("voice_call_not_found")

    @staticmethod
    def _voice_call_row(row):
        if row is None:
            return None
        return {key: row[key] for key in ("call_id","conversation_id","caller_ai_id",
            "callee_ai_id","state","created_at","expires_at","updated_at")}

    def get_voice_call(self, call_id):
        row = self._connection.execute(
            "SELECT * FROM voice_calls WHERE call_id=?", (call_id,)).fetchone()
        return self._voice_call_row(row)

    def find_active_voice_call(self, conversation_id):
        row = self._connection.execute(
            """SELECT * FROM voice_calls WHERE conversation_id=?
               AND state IN ('RINGING','ACCEPTED','CONNECTING','CONNECTED')
               ORDER BY created_at DESC LIMIT 1""", (conversation_id,)).fetchone()
        return self._voice_call_row(row)

    def append_voice_signal(self, call_id, sender_ai_id, kind, payload, created_at):
        cursor = self._connection.execute(
            """INSERT INTO voice_call_signals(call_id,sender_ai_id,kind,payload_json,created_at)
               VALUES(?,?,?,?,?)""",
            (call_id,sender_ai_id,kind,json.dumps(payload,separators=(",",":")),created_at))
        self._connection.commit()
        return {"signalId":cursor.lastrowid,"callId":call_id,"senderAiId":sender_ai_id,
                "kind":kind,"payload":payload,"createdAt":created_at}

    def delete_voice_call_signals(self, call_id):
        self._connection.execute(
            "DELETE FROM voice_call_signals WHERE call_id=?", (call_id,))
        self._connection.commit()

    def load_voice_signals(self, call_id, recipient_ai_id, after_id, limit):
        rows = self._connection.execute(
            """SELECT signal_id,call_id,sender_ai_id,kind,payload_json,created_at
               FROM voice_call_signals WHERE call_id=? AND signal_id>? AND sender_ai_id<>?
               ORDER BY signal_id LIMIT ?""",
            (call_id,after_id,recipient_ai_id,limit)).fetchall()
        return [{"signalId":row["signal_id"],"callId":row["call_id"],
                 "senderAiId":row["sender_ai_id"],"kind":row["kind"],
                 "payload":json.loads(row["payload_json"]),
                 "createdAt":row["created_at"]} for row in rows]

    def get_provider_request(self, principal_ai_id, request_id):
        row = self._connection.execute(
            "SELECT * FROM provider_request_records WHERE principal_ai_id=? AND request_id=?",
            (principal_ai_id, request_id)).fetchone()
        return dict(row) if row else None

    def claim_provider_request(self, principal_ai_id, request_id, request_digest,
                               conversation_id, agent_id, now, lease_seconds=360.0):
        """Claim a durable provider attempt; reclaim stale PROCESSING rows with a new fence."""
        if not isinstance(lease_seconds, (int, float)) or lease_seconds <= 0:
            raise ValueError("invalid_provider_lease")
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            row = self._connection.execute(
                "SELECT * FROM provider_request_records WHERE principal_ai_id=? AND request_id=?",
                (principal_ai_id, request_id)).fetchone()
            if row is not None:
                if row["request_digest"] != request_digest:
                    self._connection.rollback()
                    return dict(row), "conflict"
                if row["status"] == "COMPLETED":
                    self._connection.rollback()
                    return dict(row), "existing"
                reclaimable = (row["status"] == "FAILED" or
                               (row["status"] == "PROCESSING" and
                                float(now) - float(row["updated_at"]) >= float(lease_seconds)))
                if not reclaimable:
                    self._connection.rollback()
                    return dict(row), "existing"
                next_generation = int(row["attempt_generation"]) + 1
                cursor = self._connection.execute(
                    """UPDATE provider_request_records
                       SET status='PROCESSING',attempt_generation=?,error_code=NULL,updated_at=?
                       WHERE principal_ai_id=? AND request_id=? AND attempt_generation=?""",
                    (next_generation, now, principal_ai_id, request_id, row["attempt_generation"]))
                if cursor.rowcount != 1:
                    self._connection.rollback()
                    return dict(row), "existing"
            else:
                next_generation = 1
                self._connection.execute(
                    """INSERT INTO provider_request_records(
                       principal_ai_id,request_id,request_digest,status,conversation_id,agent_id,
                       created_at,updated_at,attempt_generation)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                    (principal_ai_id,request_id,request_digest,"PROCESSING",
                     conversation_id,agent_id,now,now,next_generation))
            claimed = self._connection.execute(
                "SELECT * FROM provider_request_records WHERE principal_ai_id=? AND request_id=?",
                (principal_ai_id, request_id)).fetchone()
            self._connection.commit()
            return dict(claimed), "claimed"
        except Exception:
            self._connection.rollback()
            raise

    def save_provider_message_and_complete(self, principal_ai_id, request_id, request_digest,
                                           message, attestation, provider_id, model, now, attempt_generation=1):
        """Atomically persist the provider message and mark its request COMPLETED."""
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            row = self._connection.execute(
                "SELECT * FROM provider_request_records WHERE principal_ai_id=? AND request_id=?",
                (principal_ai_id, request_id)).fetchone()
            if row is None or row["request_digest"] != request_digest:
                self._connection.rollback()
                raise ValueError("provider_request_not_claimed")
            if row["status"] == "COMPLETED":
                self._connection.rollback()
                return dict(row), False
            if row["status"] != "PROCESSING" or int(row["attempt_generation"]) != int(attempt_generation):
                self._connection.rollback()
                raise ValueError("provider_request_attempt_fenced")
            self._connection.execute(
                """INSERT INTO messages(
                   message_id,conversation_id,sender_ai_id,recipient_ai_ids,body,
                   client_request_id,sequence,kind,created_at_epoch_seconds)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (message.message_id, message.conversation_id, message.sender_ai_id,
                 ",".join(message.recipient_ai_ids), message.body,
                 message.client_request_id, message.sequence, message.kind,
                 message.created_at_epoch_seconds))
            self._connection.execute(
                "INSERT INTO idempotency(sender_ai_id,client_request_id,message_id) VALUES(?,?,?)",
                (message.sender_ai_id, message.client_request_id, message.message_id))
            self._connection.execute(
                """UPDATE provider_request_records
                   SET status='COMPLETED',response_text=?,provider_id=?,model=?,
                       attestation_json=?,message_id=?,updated_at=?,error_code=NULL
                   WHERE principal_ai_id=? AND request_id=? AND status='PROCESSING' AND attempt_generation=?""",
                (message.body, provider_id, model,
                 json.dumps(attestation, separators=(",", ":")),
                 message.message_id, now, principal_ai_id, request_id, attempt_generation))
            self._connection.commit()
            completed = self._connection.execute(
                "SELECT * FROM provider_request_records WHERE principal_ai_id=? AND request_id=?",
                (principal_ai_id, request_id)).fetchone()
            return dict(completed), True
        except Exception:
            self._connection.rollback()
            raise

    def complete_provider_request(self, principal_ai_id, request_id, request_digest,
                                  response_text, provider_id, model, attestation,
                                  message_id, now, attempt_generation=1):
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            row = self._connection.execute(
                "SELECT * FROM provider_request_records WHERE principal_ai_id=? AND request_id=?",
                (principal_ai_id, request_id)).fetchone()
            if row is None or row["request_digest"] != request_digest:
                self._connection.rollback()
                raise ValueError("provider_request_not_claimed")
            if row["status"] == "COMPLETED":
                self._connection.rollback()
                return dict(row)
            if row["status"] != "PROCESSING" or int(row["attempt_generation"]) != int(attempt_generation):
                self._connection.rollback()
                raise ValueError("provider_request_attempt_fenced")
            self._connection.execute(
                """UPDATE provider_request_records
                   SET status='COMPLETED',response_text=?,provider_id=?,model=?,
                       attestation_json=?,message_id=?,updated_at=?,error_code=NULL
                   WHERE principal_ai_id=? AND request_id=? AND status='PROCESSING' AND attempt_generation=?""",
                (response_text,provider_id,model,json.dumps(attestation,separators=(",",":")),
                 message_id,now,principal_ai_id,request_id,attempt_generation))
            row = self._connection.execute(
                "SELECT * FROM provider_request_records WHERE principal_ai_id=? AND request_id=?",
                (principal_ai_id, request_id)).fetchone()
            self._connection.commit()
            return dict(row)
        except Exception:
            self._connection.rollback()
            raise

    def fail_provider_request(self, principal_ai_id, request_id, request_digest,
                               error_code, now, attempt_generation=1):
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            row = self._connection.execute(
                "SELECT request_digest,status,attempt_generation FROM provider_request_records WHERE principal_ai_id=? AND request_id=?",
                (principal_ai_id, request_id)).fetchone()
            if row is None or row["request_digest"] != request_digest:
                self._connection.rollback()
                return False
            if row["status"] != "PROCESSING" or int(row["attempt_generation"]) != int(attempt_generation):
                self._connection.rollback()
                return False
            self._connection.execute(
                """UPDATE provider_request_records
                   SET status='FAILED',error_code=?,updated_at=?
                   WHERE principal_ai_id=? AND request_id=? AND status='PROCESSING' AND attempt_generation=?""",
                (error_code,now,principal_ai_id,request_id,attempt_generation))
            self._connection.commit()
            return True
        except Exception:
            self._connection.rollback()
            raise

    def close(self):
        self._connection.close()

    def save_conversation(self, conversation_id: str, member_ai_ids: List[str], kind: str = "GROUP"):
        self._connection.execute(
            "INSERT OR REPLACE INTO conversations(conversation_id, member_ai_ids, kind) VALUES(?,?,?)",
            (conversation_id, ",".join(sorted(set(member_ai_ids))), kind),
        )
        self._connection.commit()

    def load_conversations(self) -> Dict[str, set]:
        rows = self._connection.execute("SELECT conversation_id, member_ai_ids, kind FROM conversations").fetchall()
        return {r["conversation_id"]: set(filter(None, r["member_ai_ids"].split(","))) for r in rows}

    def load_conversation_kinds(self) -> Dict[str, str]:
        rows = self._connection.execute("SELECT conversation_id, kind FROM conversations").fetchall()
        return {r["conversation_id"]: (r["kind"] or "GROUP") for r in rows}

    def save_message_with_idempotency(self, message: Tuple[str,str,str,Tuple[str,...],str,str,int,str,float]):
        kind = message[7] if len(message) > 7 else "NORMAL"
        created_at = message[8] if len(message) > 8 else time.time()
        self._connection.execute("BEGIN")
        try:
            self._connection.execute(
                "INSERT INTO messages(message_id,conversation_id,sender_ai_id,recipient_ai_ids,body,client_request_id,sequence,kind,created_at_epoch_seconds) VALUES(?,?,?,?,?,?,?,?,?)",
                (message[0],message[1],message[2],",".join(message[3]),message[4],message[5],message[6],kind,created_at),
            )
            self._connection.execute(
                "INSERT INTO idempotency(sender_ai_id,client_request_id,message_id) VALUES(?,?,?)",
                (message[2],message[5],message[0]),
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def save_message(self, message: Tuple[str,str,str,Tuple[str,...],str,str,int,str,float]):
        kind = message[7] if len(message) > 7 else "NORMAL"
        created_at = message[8] if len(message) > 8 else time.time()
        self._connection.execute(
            "INSERT INTO messages(message_id,conversation_id,sender_ai_id,recipient_ai_ids,body,client_request_id,sequence,kind,created_at_epoch_seconds) VALUES(?,?,?,?,?,?,?,?,?)",
            (message[0],message[1],message[2],",".join(message[3]),message[4],message[5],message[6],kind,created_at),
        )
        self._connection.commit()

    def load_messages(self):
        return self._connection.execute(
            "SELECT message_id,conversation_id,sender_ai_id,recipient_ai_ids,body,client_request_id,sequence,kind,created_at_epoch_seconds FROM messages ORDER BY sequence"
        ).fetchall()

    def save_idempotency(self, sender_ai_id: str, client_request_id: str, message_id: str):
        self._connection.execute(
            "INSERT INTO idempotency(sender_ai_id,client_request_id,message_id) VALUES(?,?,?)",
            (sender_ai_id,client_request_id,message_id),
        )
        self._connection.commit()

    def find_idempotency(self, sender_ai_id: str, client_request_id: str) -> Optional[str]:
        row=self._connection.execute(
            "SELECT message_id FROM idempotency WHERE sender_ai_id=? AND client_request_id=?",
            (sender_ai_id,client_request_id),
        ).fetchone()
        return row["message_id"] if row else None

    def delete_message(self, message_id: str) -> bool:
        self._connection.execute("DELETE FROM audio_attachments WHERE message_id=?", (message_id,))
        self._connection.execute("DELETE FROM acknowledgements WHERE message_id=?", (message_id,))
        self._connection.execute("DELETE FROM idempotency WHERE message_id=?", (message_id,))
        cursor = self._connection.execute("DELETE FROM messages WHERE message_id=?", (message_id,))
        self._connection.commit()
        return cursor.rowcount == 1

    def save_ack(self, message_id: str, ai_id: str) -> bool:
        if (not isinstance(message_id, str) or not message_id.strip()
                or not isinstance(ai_id, str) or not ai_id.strip()):
            raise ValueError("invalid_ack_identity")
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            message = self._connection.execute(
                "SELECT conversation_id,recipient_ai_ids FROM messages WHERE message_id=?",
                (message_id,)).fetchone()
            if message is None:
                raise ValueError("ack_message_not_found")
            recipients = set(filter(None, message["recipient_ai_ids"].split(",")))
            if ai_id not in recipients:
                raise ValueError("ack_recipient_required")
            conversation = self._connection.execute(
                "SELECT member_ai_ids FROM conversations WHERE conversation_id=?",
                (message["conversation_id"],)).fetchone()
            members = (set(filter(None, conversation["member_ai_ids"].split(",")))
                       if conversation is not None else set())
            if ai_id not in members:
                raise ValueError("ack_room_membership_required")
            cursor = self._connection.execute(
                "INSERT OR IGNORE INTO acknowledgements(message_id,ai_id) VALUES(?,?)",
                (message_id, ai_id))
            self._connection.commit()
            return cursor.rowcount == 1
        except Exception:
            self._connection.rollback()
            raise

    def load_acknowledgements(self) -> Dict[str,set]:
        rows=self._connection.execute("SELECT message_id,ai_id FROM acknowledgements").fetchall()
        result={}
        for row in rows:
            result.setdefault(row["message_id"],set()).add(row["ai_id"])
        return result


    def save_audio_attachment(self, attachment: Tuple[str,str,str,str,str,int,str]):
        self._connection.execute(
            """INSERT INTO audio_attachments(
                object_id,message_id,conversation_id,sender_ai_id,content_type,size,sha256
            ) VALUES(?,?,?,?,?,?,?)""",
            attachment,
        )
        self._connection.commit()

    def load_audio_attachments_for_message(self, message_id: str):
        return self._connection.execute(
            """SELECT object_id,message_id,conversation_id,sender_ai_id,content_type,size,sha256,created_at
               FROM audio_attachments WHERE message_id=? ORDER BY object_id""",
            (message_id,),
        ).fetchall()

    def delete_audio_attachment(self, object_id: str) -> bool:
        cursor = self._connection.execute(
            "DELETE FROM audio_attachments WHERE object_id=?", (object_id,))
        self._connection.commit()
        return cursor.rowcount == 1

    def save_conversation_admin(self, conversation_id: str, ai_id: str):
        self._connection.execute(
            "INSERT OR IGNORE INTO conversation_admins(conversation_id,ai_id) VALUES(?,?)",
            (conversation_id, ai_id))
        self._connection.commit()

    def is_conversation_admin(self, conversation_id: str, ai_id: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM conversation_admins WHERE conversation_id=? AND ai_id=?",
            (conversation_id, ai_id)).fetchone()
        return row is not None

    def create_room_invite(self, invite):
        self._connection.execute(
            """INSERT INTO room_invites(invite_id,conversation_id,token_hash,
               created_by_ai_id,created_at,expires_at,max_uses,uses,revoked_at)
               VALUES(?,?,?,?,?,?,?,0,NULL)""",
            tuple(invite[key] for key in ("invite_id","conversation_id","token_hash",
                "created_by_ai_id","created_at","expires_at","max_uses")))
        self._connection.commit()

    def get_room_invite(self, invite_id):
        row = self._connection.execute(
            "SELECT * FROM room_invites WHERE invite_id=?", (invite_id,)).fetchone()
        return dict(row) if row else None

    def find_room_invite_by_hash(self, token_hash):
        row = self._connection.execute(
            "SELECT * FROM room_invites WHERE token_hash=?", (token_hash,)).fetchone()
        return dict(row) if row else None

    def list_room_invites(self, conversation_id):
        rows = self._connection.execute(
            """SELECT invite_id,conversation_id,created_by_ai_id,created_at,
               expires_at,max_uses,uses,revoked_at FROM room_invites
               WHERE conversation_id=? ORDER BY created_at DESC""",
            (conversation_id,)).fetchall()
        return [dict(row) for row in rows]

    def revoke_room_invite(self, invite_id, conversation_id, revoked_at):
        cursor = self._connection.execute(
            """UPDATE room_invites SET revoked_at=?
               WHERE invite_id=? AND conversation_id=? AND revoked_at IS NULL""",
            (revoked_at, invite_id, conversation_id))
        self._connection.commit()
        return cursor.rowcount == 1

    def create_join_request(self, request):
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            invite = self._connection.execute(
                "SELECT uses,max_uses,expires_at,revoked_at FROM room_invites WHERE invite_id=?",
                (request["invite_id"],)).fetchone()
            if (invite is None or invite["revoked_at"] is not None or
                    invite["expires_at"] <= request["created_at"] or
                    invite["uses"] >= invite["max_uses"]):
                self._connection.rollback()
                return None, "invite_unavailable"
            existing = self._connection.execute(
                "SELECT * FROM join_requests WHERE invite_id=? AND ai_id=?",
                (request["invite_id"], request["ai_id"])).fetchone()
            if existing:
                self._connection.rollback()
                return dict(existing), "request_exists"
            self._connection.execute(
                """INSERT INTO join_requests(request_id,invite_id,conversation_id,
                   ai_id,status,created_at,decided_at,decided_by_ai_id)
                   VALUES(?,?,?,?, 'PENDING', ?,NULL,NULL)""",
                (request["request_id"],request["invite_id"],request["conversation_id"],
                 request["ai_id"],request["created_at"]))
            self._connection.execute(
                "UPDATE room_invites SET uses=uses+1 WHERE invite_id=?",
                (request["invite_id"],))
            self._connection.commit()
            return self._connection.execute(
                "SELECT * FROM join_requests WHERE request_id=?",
                (request["request_id"],)).fetchone(), "created"
        except Exception:
            self._connection.rollback()
            raise

    def list_join_requests(self, conversation_id, status="PENDING"):
        rows = self._connection.execute(
            """SELECT request_id,invite_id,conversation_id,ai_id,status,created_at,
               decided_at,decided_by_ai_id FROM join_requests
               WHERE conversation_id=? AND status=? ORDER BY created_at,request_id""",
            (conversation_id,status)).fetchall()
        return [dict(row) for row in rows]

    def decide_join_request(self, conversation_id, request_id, decision,
                            decided_by_ai_id, decided_at, members):
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            row = self._connection.execute(
                """SELECT * FROM join_requests WHERE request_id=?
                   AND conversation_id=?""", (request_id,conversation_id)).fetchone()
            if row is None:
                self._connection.rollback()
                return None, "request_not_found"
            if row["status"] != "PENDING":
                self._connection.rollback()
                return dict(row), "request_already_decided"
            if decision == "APPROVE":
                current = self._connection.execute(
                    "SELECT member_ai_ids FROM conversations WHERE conversation_id=?",
                    (conversation_id,)).fetchone()
                if current is None:
                    self._connection.rollback()
                    return None, "conversation_not_found"
                current_members = set(filter(None,current["member_ai_ids"].split(",")))
                if row["ai_id"] not in current_members:
                    if len(current_members) >= members:
                        self._connection.rollback()
                        return None, "conversation_member_limit"
                    current_members.add(row["ai_id"])
                    self._connection.execute(
                        "UPDATE conversations SET member_ai_ids=? WHERE conversation_id=?",
                        (",".join(sorted(current_members)),conversation_id))
            final_status = "APPROVED" if decision == "APPROVE" else "REJECTED"
            self._connection.execute(
                """UPDATE join_requests SET status=?,decided_at=?,decided_by_ai_id=?
                   WHERE request_id=? AND status='PENDING'""",
                (final_status,decided_at,decided_by_ai_id,request_id))
            self._connection.commit()
            result = self._connection.execute(
                "SELECT * FROM join_requests WHERE request_id=?", (request_id,)).fetchone()
            return dict(result), "decided"
        except Exception:
            self._connection.rollback()
            raise
