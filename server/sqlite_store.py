import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCHEMA_VERSION = 3

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

        if version < 2:
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS tool_permissions (
                    principal_ai_id TEXT NOT NULL,
                    tool_id TEXT NOT NULL,
                    granted_by TEXT NOT NULL,
                    granted_at TEXT NOT NULL,
                    PRIMARY KEY(principal_ai_id, tool_id)
                );
            """)
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','2')")
            self._connection.commit()

        if version < 3:
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS tool_permission_audit (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL CHECK(action IN ('GRANT', 'REVOKE')),
                    principal_ai_id TEXT NOT NULL,
                    tool_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    grant_existed INTEGER NOT NULL CHECK(grant_existed IN (0, 1))
                );
                CREATE INDEX IF NOT EXISTS idx_tool_permission_audit_subject
                    ON tool_permission_audit(principal_ai_id, tool_id, audit_id);
                CREATE TRIGGER IF NOT EXISTS trg_tool_permission_audit_no_update
                    BEFORE UPDATE ON tool_permission_audit
                    BEGIN SELECT RAISE(ABORT, 'tool_permission_audit_immutable'); END;
                CREATE TRIGGER IF NOT EXISTS trg_tool_permission_audit_no_delete
                    BEFORE DELETE ON tool_permission_audit
                    BEGIN SELECT RAISE(ABORT, 'tool_permission_audit_immutable'); END;
            """)
            self._connection.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('version','3')")
            self._connection.commit()



    def grant_tool_permission(self, principal_ai_id: str, tool_id: str,
                              granted_by: str, granted_at: str):
        self._connection.execute("BEGIN")
        try:
            self._connection.execute(
                """INSERT INTO tool_permissions(principal_ai_id,tool_id,granted_by,granted_at)
                   VALUES(?,?,?,?)
                   ON CONFLICT(principal_ai_id,tool_id)
                   DO UPDATE SET granted_by=excluded.granted_by, granted_at=excluded.granted_at""",
                (principal_ai_id, tool_id, granted_by, granted_at),
            )
            self._connection.execute(
                """INSERT INTO tool_permission_audit
                   (action,principal_ai_id,tool_id,actor_id,occurred_at,grant_existed)
                   VALUES('GRANT',?,?,?,?,1)""",
                (principal_ai_id, tool_id, granted_by, granted_at),
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def revoke_tool_permission(self, principal_ai_id: str, tool_id: str,
                                revoked_by: str, revoked_at: str) -> bool:
        self._connection.execute("BEGIN")
        try:
            cursor = self._connection.execute(
                "DELETE FROM tool_permissions WHERE principal_ai_id=? AND tool_id=?",
                (principal_ai_id, tool_id),
            )
            existed = cursor.rowcount > 0
            self._connection.execute(
                """INSERT INTO tool_permission_audit
                   (action,principal_ai_id,tool_id,actor_id,occurred_at,grant_existed)
                   VALUES('REVOKE',?,?,?,?,?)""",
                (principal_ai_id, tool_id, revoked_by, revoked_at, int(existed)),
            )
            self._connection.commit()
            return existed
        except Exception:
            self._connection.rollback()
            raise

    def load_tool_permission_audit(self):
        return self._connection.execute(
            """SELECT audit_id,action,principal_ai_id,tool_id,actor_id,occurred_at,grant_existed
               FROM tool_permission_audit ORDER BY audit_id"""
        ).fetchall()

    def load_tool_permissions(self):
        return self._connection.execute(
            """SELECT principal_ai_id,tool_id,granted_by,granted_at
               FROM tool_permissions ORDER BY principal_ai_id,tool_id"""
        ).fetchall()

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
