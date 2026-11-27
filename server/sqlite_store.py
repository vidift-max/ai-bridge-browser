import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCHEMA_VERSION = 2


class SQLiteMessengerStore:
    """Small stdlib-only durable store for the experimental Messenger backend."""

    def __init__(self, path: str):
        if not path:
            raise ValueError("storage_path_required")
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path, check_same_thread=False)
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

            db.commit()
        except Exception:
            db.rollback()
            raise

    def close(self):
        self._connection.close()

    def save_conversation(self, conversation_id: str, member_ai_ids: List[str]):
        self._connection.execute(
            "INSERT OR REPLACE INTO conversations(conversation_id, member_ai_ids) VALUES(?,?)",
            (conversation_id, ",".join(sorted(set(member_ai_ids)))),
        )
        self._connection.commit()

    def load_conversations(self) -> Dict[str, set]:
        rows = self._connection.execute("SELECT conversation_id, member_ai_ids FROM conversations").fetchall()
        return {r["conversation_id"]: set(filter(None, r["member_ai_ids"].split(","))) for r in rows}

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
