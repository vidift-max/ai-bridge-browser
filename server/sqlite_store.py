import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCHEMA_VERSION = 5

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
