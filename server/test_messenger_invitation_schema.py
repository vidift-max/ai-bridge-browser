import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.backup import validate_restore_candidate
from server.recovery import verify_messenger_schema
from server.sqlite_store import SQLiteMessengerStore


class MessengerInvitationSchemaTests(unittest.TestCase):
    def test_fresh_database_migrates_to_v4(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fresh.sqlite"
            store = SQLiteMessengerStore(str(path))
            version = store._connection.execute(
                "SELECT value FROM schema_meta WHERE key='version'"
            ).fetchone()[0]
            store.close()
            self.assertEqual(version, "4")
            self.assertEqual(verify_messenger_schema(str(path)),
                             (True, "RESTORE_SCHEMA_COMPATIBLE"))

    def test_v1_database_migrates_without_losing_messages(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.save_conversation("room-1", ["AI-A", "AI-B"])
            store.save_message_with_idempotency(
                ("m-1", "room-1", "AI-A", ("AI-B",), "hello", "req-1", 1)
            )
            store.close()
            with sqlite3.connect(path) as db:
                db.execute("DROP TABLE invitations")
                db.execute("UPDATE schema_meta SET value='1' WHERE key='version'")
            reopened = SQLiteMessengerStore(str(path))
            self.assertEqual(reopened.load_conversations()["room-1"], {"AI-A", "AI-B"})
            self.assertEqual(reopened.load_messages()[0]["message_id"], "m-1")
            self.assertEqual(reopened.find_idempotency("AI-A", "req-1"), "m-1")
            reopened.close()
            self.assertEqual(verify_messenger_schema(str(path)),
                             (True, "RESTORE_SCHEMA_COMPATIBLE"))

    def test_v2_database_migrates_to_v4_and_preserves_invitations(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v2.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.save_conversation("room-1", ["AI-A", "AI-B"])
            store._connection.execute(
                "INSERT INTO invitations(invitation_id,conversation_id,target_ai_id,token_hash,status,"
                "created_by_ai_id,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?)",
                ("inv-v2", "room-1", "AI-C", "c" * 64, "PENDING", "AI-A", 100, 200),
            )
            store._connection.commit()
            store.close()
            with sqlite3.connect(path) as db:
                db.execute("ALTER TABLE conversations DROP COLUMN conversation_kind")
                db.execute("UPDATE schema_meta SET value='2' WHERE key='version'")
            migrated = SQLiteMessengerStore(str(path))
            try:
                version = migrated._connection.execute(
                    "SELECT value FROM schema_meta WHERE key='version'"
                ).fetchone()[0]
                kind = migrated._connection.execute(
                    "SELECT conversation_kind FROM conversations WHERE conversation_id='room-1'"
                ).fetchone()[0]
                invitation = migrated._connection.execute(
                    "SELECT status, token_hash FROM invitations WHERE invitation_id='inv-v2'"
                ).fetchone()
                self.assertEqual(version, "4")
                self.assertEqual(kind, "GROUP")
                self.assertEqual(invitation["status"], "PENDING")
                self.assertEqual(invitation["token_hash"], "c" * 64)
            finally:
                migrated.close()

    def test_v3_database_migrates_to_v4_rate_limit_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v3.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.close()
            with sqlite3.connect(path) as db:
                db.execute("DROP TABLE rate_limit_events")
                db.execute("UPDATE schema_meta SET value='3' WHERE key='version'")
            migrated = SQLiteMessengerStore(str(path))
            try:
                version = migrated._connection.execute(
                    "SELECT value FROM schema_meta WHERE key='version'"
                ).fetchone()[0]
                columns = {row[1] for row in migrated._connection.execute(
                    "PRAGMA table_info(rate_limit_events)")}
                self.assertEqual(version, "4")
                self.assertEqual(columns, {"event_id", "principal", "event_at"})
                self.assertEqual(verify_messenger_schema(str(path)),
                                 (True, "RESTORE_SCHEMA_COMPATIBLE"))
            finally:
                migrated.close()
    def test_future_schema_is_rejected_without_downgrade(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "future.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.close()
            with sqlite3.connect(path) as db:
                db.execute("UPDATE schema_meta SET value='999' WHERE key='version'")
            with self.assertRaises(RuntimeError):
                SQLiteMessengerStore(str(path))
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute(
                    "SELECT value FROM schema_meta WHERE key='version'"
                ).fetchone()[0], "999")

    def test_v2_restore_candidate_accepts_valid_pending_invitation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.save_conversation("room-1", ["AI-A", "AI-B"])
            store._connection.execute(
                "INSERT INTO invitations(invitation_id,conversation_id,target_ai_id,token_hash,status,"
                "created_by_ai_id,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?)",
                ("inv-1", "room-1", "AI-C", "a" * 64, "PENDING", "AI-A", 100, 200),
            )
            store._connection.commit()
            store.close()
            self.assertEqual(validate_restore_candidate(str(path)),
                             (True, "RESTORE_CANDIDATE_VALIDATED"))

    def test_restore_rejects_invitation_with_unknown_creator(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.save_conversation("room-1", ["AI-A", "AI-B"])
            store._connection.execute(
                "INSERT INTO invitations(invitation_id,conversation_id,target_ai_id,token_hash,status,"
                "created_by_ai_id,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?)",
                ("inv-1", "room-1", "AI-C", "b" * 64, "PENDING", "AI-X", 100, 200),
            )
            store._connection.commit()
            store.close()
            self.assertEqual(validate_restore_candidate(str(path)),
                             (False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"))

    def test_v1_restore_candidate_remains_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.sqlite"
            store = SQLiteMessengerStore(str(path))
            store.save_conversation("room-1", ["AI-A", "AI-B"])
            store.close()
            with sqlite3.connect(path) as db:
                db.execute("DROP TABLE invitations")
                db.execute("UPDATE schema_meta SET value='1' WHERE key='version'")
            self.assertEqual(verify_messenger_schema(str(path)),
                             (True, "RESTORE_SCHEMA_COMPATIBLE"))
            self.assertEqual(validate_restore_candidate(str(path)),
                             (True, "RESTORE_CANDIDATE_VALIDATED"))


if __name__ == "__main__":
    unittest.main()
