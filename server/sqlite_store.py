import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCHEMA_VERSION = 4


class SQLiteMessengerStore:
    """Small stdlib-only durable store for the experimental Messenger backend."""

    def __init__(self, path: str):
        if not path:
            raise ValueError("storage_path_required")
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        self._connection = sqlite3.connect(path, check_same_thread=False, timeout=10)
        self._connection.execute("PRAGMA busy_timeout=10000")
        self._connection.row_factory = sqlite3.Row
        try:
            self._migrate()
        except Exception:
            self._connection.close()
            raise

    def _migrate(self):
        db = self._connection
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute("CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            row = db.execute("SELECT value FROM schema_meta WHERE key='version'").fetchone()
            version = int(row["value"]) if row else 0
            if version > SCHEMA_VERSION or version < 0:
                raise RuntimeError("unsupported_schema_version")

            if version == 0:
                db.execute("""CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY, member_ai_ids TEXT NOT NULL)""")
                db.execute("""CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL,
                    sender_ai_id TEXT NOT NULL, recipient_ai_ids TEXT NOT NULL,
                    body TEXT NOT NULL, client_request_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL)""")
                db.execute("""CREATE TABLE IF NOT EXISTS idempotency (
                    sender_ai_id TEXT NOT NULL, client_request_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    PRIMARY KEY(sender_ai_id, client_request_id))""")
                db.execute("""CREATE TABLE IF NOT EXISTS acknowledgements (
                    message_id TEXT NOT NULL, ai_id TEXT NOT NULL,
                    PRIMARY KEY(message_id, ai_id))""")
                db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_conversation_sequence
                    ON messages(conversation_id, sequence)""")
                version = 1
                db.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','1')")

            if version == 1:
                db.execute("""CREATE TABLE invitations (
                    invitation_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    target_ai_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL CHECK(status IN ('PENDING','ACCEPTED','REVOKED','EXPIRED')),
                    created_by_ai_id TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    accepted_at INTEGER,
                    revoked_at INTEGER,
                    CHECK(length(invitation_id) BETWEEN 1 AND 200),
                    CHECK(length(conversation_id) BETWEEN 1 AND 200),
                    CHECK(length(target_ai_id) BETWEEN 1 AND 200),
                    CHECK(length(token_hash) = 64),
                    CHECK(created_at >= 0),
                    CHECK(expires_at > created_at),
                    CHECK((status = 'ACCEPTED' AND accepted_at IS NOT NULL AND revoked_at IS NULL)
                       OR (status = 'REVOKED' AND revoked_at IS NOT NULL AND accepted_at IS NULL)
                       OR (status IN ('PENDING','EXPIRED') AND accepted_at IS NULL AND revoked_at IS NULL))
                )""")
                db.execute("CREATE INDEX idx_invitations_conversation_status ON invitations(conversation_id, status)")
                db.execute("CREATE INDEX idx_invitations_target_status ON invitations(target_ai_id, status)")
                version = 2
                db.execute("UPDATE schema_meta SET value='2' WHERE key='version'")

            if version == 2:
                columns = {row[1] for row in db.execute("PRAGMA table_info(conversations)")}
                if "conversation_kind" not in columns:
                    db.execute("ALTER TABLE conversations ADD COLUMN conversation_kind TEXT NOT NULL DEFAULT 'GROUP' CHECK(conversation_kind IN ('PRIVATE','GROUP'))")
                version = 3
                db.execute("UPDATE schema_meta SET value='3' WHERE key='version'")

            if version == 3:
                db.execute("CREATE TABLE rate_limit_events (event_id INTEGER PRIMARY KEY AUTOINCREMENT, principal TEXT NOT NULL, event_at REAL NOT NULL)")
                db.execute("CREATE INDEX idx_rate_limit_principal_time ON rate_limit_events(principal,event_at)")
                version = 4
                db.execute("UPDATE schema_meta SET value='4' WHERE key='version'")

            db.commit()
        except Exception:
            db.rollback()
            raise

    def close(self):
        self._connection.close()

    def consume_rate_limit(self, principal: str, now: float, window_seconds: int, max_events: int) -> bool:
        if not principal or window_seconds < 1 or max_events < 1:
            raise ValueError("rate_limit_configuration_invalid")
        owns_connection = self._path != ":memory:"
        db = sqlite3.connect(self._path, timeout=10) if owns_connection else self._connection
        if owns_connection:
            db.execute("PRAGMA busy_timeout=10000")
        try:
            db.execute("BEGIN IMMEDIATE")
            cutoff = now - window_seconds
            db.execute("DELETE FROM rate_limit_events WHERE event_at <= ?", (cutoff,))
            count = db.execute("SELECT COUNT(*) FROM rate_limit_events WHERE principal=? AND event_at>?", (principal, cutoff)).fetchone()[0]
            if count >= max_events:
                db.commit()
                return False
            db.execute("INSERT INTO rate_limit_events(principal,event_at) VALUES(?,?)", (principal, now))
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            if owns_connection:
                db.close()

    def save_conversation(self, conversation_id: str, member_ai_ids: List[str], kind: str = "GROUP"):
        self._connection.execute(
            "INSERT OR REPLACE INTO conversations(conversation_id, member_ai_ids, conversation_kind) VALUES(?,?,?)",
            (conversation_id, ",".join(sorted(set(member_ai_ids))), kind),
        )
        self._connection.commit()

    def create_invitation(self, invitation_id: str, conversation_id: str, target_ai_id: str,
                          token_hash: str, created_by_ai_id: str, created_at: int,
                          expires_at: int) -> None:
        db = self._connection
        db.execute("BEGIN IMMEDIATE")
        try:
            row = db.execute(
                "SELECT member_ai_ids, conversation_kind FROM conversations WHERE conversation_id=?",
                (conversation_id,),
            ).fetchone()
            if row is None:
                raise ValueError("conversation_not_found")
            members = set(filter(None, row["member_ai_ids"].split(",")))
            if created_by_ai_id not in members:
                raise PermissionError("authorization_denied")
            if row["conversation_kind"] == "PRIVATE":
                raise ValueError("private_conversation_cannot_expand")
            if target_ai_id in members:
                raise ValueError("target_already_member")
            db.execute(
                "INSERT INTO invitations(invitation_id,conversation_id,target_ai_id,token_hash,status,"
                "created_by_ai_id,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?)",
                (invitation_id, conversation_id, target_ai_id, token_hash, "PENDING",
                 created_by_ai_id, created_at, expires_at),
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

    def accept_invitation(self, token_hash: str, target_ai_id: str, accepted_at: int,
                          max_members: int = 20) -> tuple[str, set]:
        db = self._connection
        db.execute("BEGIN IMMEDIATE")
        try:
            invitation = db.execute(
                "SELECT invitation_id, conversation_id, target_ai_id, status, expires_at "
                "FROM invitations WHERE token_hash=?", (token_hash,),
            ).fetchone()
            if (invitation is None or invitation["target_ai_id"] != target_ai_id
                    or invitation["status"] != "PENDING"):
                raise ValueError("invitation_unavailable")
            if invitation["expires_at"] <= accepted_at:
                db.execute("UPDATE invitations SET status='EXPIRED' WHERE invitation_id=? AND status='PENDING'",
                           (invitation["invitation_id"],))
                db.commit()
                raise ValueError("invitation_unavailable")
            conversation = db.execute(
                "SELECT member_ai_ids, conversation_kind FROM conversations WHERE conversation_id=?",
                (invitation["conversation_id"],),
            ).fetchone()
            if conversation is None:
                raise ValueError("invitation_unavailable")
            members = set(filter(None, conversation["member_ai_ids"].split(",")))
            if target_ai_id in members:
                raise ValueError("invitation_unavailable")
            if conversation["conversation_kind"] == "PRIVATE" or len(members) >= max_members:
                raise ValueError("conversation_member_limit")
            members.add(target_ai_id)
            changed = db.execute(
                "UPDATE invitations SET status='ACCEPTED', accepted_at=? "
                "WHERE invitation_id=? AND status='PENDING' AND expires_at>?",
                (accepted_at, invitation["invitation_id"], accepted_at),
            ).rowcount
            if changed != 1:
                raise ValueError("invitation_unavailable")
            db.execute("UPDATE conversations SET member_ai_ids=? WHERE conversation_id=?",
                       (",".join(sorted(members)), invitation["conversation_id"]))
            db.commit()
            return invitation["conversation_id"], members
        except Exception:
            db.rollback()
            raise

    def revoke_invitation(self, invitation_id: str, actor_ai_id: str, revoked_at: int) -> None:
        db = self._connection
        db.execute("BEGIN IMMEDIATE")
        try:
            row = db.execute(
                "SELECT created_by_ai_id, status FROM invitations WHERE invitation_id=?",
                (invitation_id,),
            ).fetchone()
            if row is None or row["created_by_ai_id"] != actor_ai_id or row["status"] != "PENDING":
                raise ValueError("invitation_unavailable")
            changed = db.execute(
                "UPDATE invitations SET status='REVOKED', revoked_at=? "
                "WHERE invitation_id=? AND status='PENDING'",
                (revoked_at, invitation_id),
            ).rowcount
            if changed != 1:
                raise ValueError("invitation_unavailable")
            db.commit()
        except Exception:
            db.rollback()
            raise

    def load_conversations(self) -> Dict[str, set]:
        rows = self._connection.execute("SELECT conversation_id, member_ai_ids FROM conversations").fetchall()
        return {r["conversation_id"]: set(filter(None, r["member_ai_ids"].split(","))) for r in rows}

    def load_conversation_members(self, conversation_id: str) -> set:
        row = self._connection.execute(
            "SELECT member_ai_ids FROM conversations WHERE conversation_id=?",
            (conversation_id,),
        ).fetchone()
        return set(filter(None, row["member_ai_ids"].split(","))) if row else set()

    def save_message_with_idempotency(self, message: Tuple[str,str,str,Tuple[str,...],str,str,int]):
        self._connection.execute("BEGIN")
        try:
            self._connection.execute(
                "INSERT INTO messages(message_id,conversation_id,sender_ai_id,recipient_ai_ids,body,client_request_id,sequence) VALUES(?,?,?,?,?,?,?)",
                (message[0],message[1],message[2],",".join(message[3]),message[4],message[5],message[6]),
            )
            self._connection.execute(
                "INSERT INTO idempotency(sender_ai_id,client_request_id,message_id) VALUES(?,?,?)",
                (message[2],message[5],message[0]),
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def save_message(self, message: Tuple[str,str,str,Tuple[str,...],str,str,int]):
        self._connection.execute(
            "INSERT INTO messages(message_id,conversation_id,sender_ai_id,recipient_ai_ids,body,client_request_id,sequence) VALUES(?,?,?,?,?,?,?)",
            (message[0],message[1],message[2],",".join(message[3]),message[4],message[5],message[6]),
        )
        self._connection.commit()

    def load_messages(self):
        return self._connection.execute(
            "SELECT message_id,conversation_id,sender_ai_id,recipient_ai_ids,body,client_request_id,sequence FROM messages ORDER BY sequence"
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

    def save_ack(self, message_id: str, ai_id: str):
        self._connection.execute(
            "INSERT OR IGNORE INTO acknowledgements(message_id,ai_id) VALUES(?,?)",
            (message_id,ai_id),
        )
        self._connection.commit()

    def load_acknowledgements(self) -> Dict[str,set]:
        rows=self._connection.execute("SELECT message_id,ai_id FROM acknowledgements").fetchall()
        result={}
        for row in rows:
            result.setdefault(row["message_id"],set()).add(row["ai_id"])
        return result
