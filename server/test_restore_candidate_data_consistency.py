import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from server.backup import validate_restore_candidate
from server.sqlite_store import SQLiteMessengerStore


class RestoreCandidateDataConsistencyTests(unittest.TestCase):
    def _candidate(self, directory):
        path = Path(directory) / "candidate.sqlite"
        store = SQLiteMessengerStore(str(path))
        store.save_conversation("room-1", ["AI-A", "AI-B"])
        store.save_message_with_idempotency(
            ("m-1", "room-1", "AI-A", ("AI-B",), "hello", "req-1", 1)
        )
        store.save_ack("m-1", "AI-B")
        store.close()
        return path

    def test_consistent_candidate_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            self.assertEqual(validate_restore_candidate(str(path)),
                             (True, "RESTORE_CANDIDATE_VALIDATED"))

    def test_orphan_conversation_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE messages SET conversation_id='missing-room'")
            self.assertEqual(validate_restore_candidate(str(path)),
                             (False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"))

    def test_sender_outside_conversation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE messages SET sender_ai_id='AI-X'")
            self.assertEqual(validate_restore_candidate(str(path)),
                             (False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"))

    def test_recipient_outside_conversation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE messages SET recipient_ai_ids='AI-X'")
            self.assertEqual(validate_restore_candidate(str(path)),
                             (False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"))

    def test_orphan_or_mismatched_idempotency_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE idempotency SET message_id='missing-message'")
            self.assertEqual(validate_restore_candidate(str(path)),
                             (False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"))

    def test_acknowledgement_for_non_member_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE acknowledgements SET ai_id='AI-X'")
            self.assertEqual(validate_restore_candidate(str(path)),
                             (False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"))

    def test_non_positive_sequence_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE messages SET sequence=0")
            self.assertEqual(validate_restore_candidate(str(path)),
                             (False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"))

    def test_validation_does_not_modify_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with sqlite3.connect(path) as db:
                before = db.execute("SELECT * FROM messages").fetchall()
            self.assertEqual(validate_restore_candidate(str(path)),
                             (True, "RESTORE_CANDIDATE_VALIDATED"))
            with sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True) as db:
                after = db.execute("SELECT * FROM messages").fetchall()
            self.assertEqual(after, before)


    def test_empty_member_list_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE conversations SET member_ai_ids=''")
            self.assertEqual(validate_restore_candidate(str(path)),
                             (False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"))

    def test_malformed_recipient_delimiters_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE messages SET recipient_ai_ids='AI-B,,AI-A'")
            self.assertEqual(validate_restore_candidate(str(path)),
                             (False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"))

    def test_whitespace_padded_identifier_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE conversations SET member_ai_ids='AI-A, AI-B'")
            self.assertEqual(validate_restore_candidate(str(path)),
                             (False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"))

    def test_non_text_identifier_storage_is_rejected_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE messages SET recipient_ai_ids=?", (sqlite3.Binary(b"AI-B"),))
            self.assertEqual(validate_restore_candidate(str(path)),
                             (False, "RESTORE_CANDIDATE_DATA_INCONSISTENT"))


    def test_validation_uses_one_sqlite_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with patch("server.backup.sqlite3.connect", wraps=sqlite3.connect) as connect:
                self.assertEqual(validate_restore_candidate(str(path)),
                                 (True, "RESTORE_CANDIDATE_VALIDATED"))
                self.assertEqual(connect.call_count, 1)

    def test_validation_keeps_one_snapshot_during_concurrent_wal_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with sqlite3.connect(path) as setup:
                setup.execute("PRAGMA journal_mode=WAL")
            import server.recovery as recovery
            original = recovery._verify_sqlite_recovery_connection
            changed = []

            def integrity_then_concurrent_write(connection):
                result = original(connection)
                if not changed:
                    with sqlite3.connect(path) as writer:
                        writer.execute("UPDATE messages SET sender_ai_id='AI-X'")
                    changed.append(True)
                return result

            with patch("server.recovery._verify_sqlite_recovery_connection",
                       side_effect=integrity_then_concurrent_write):
                self.assertEqual(validate_restore_candidate(str(path)),
                                 (True, "RESTORE_CANDIDATE_VALIDATED"))
            self.assertTrue(changed)
            self.assertEqual(
                recovery.verify_messenger_data_consistency(str(path)),
                (False, "RESTORE_DATA_MESSAGE_INVALID"),
            )


    def test_validation_closes_connection_after_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            connections = []
            real_connect = sqlite3.connect

            def tracked_connect(*args, **kwargs):
                connection = real_connect(*args, **kwargs)
                connections.append(connection)
                return connection

            with patch("server.backup.sqlite3.connect", side_effect=tracked_connect):
                self.assertEqual(validate_restore_candidate(str(path)),
                                 (True, "RESTORE_CANDIDATE_VALIDATED"))
            self.assertEqual(len(connections), 1)
            with self.assertRaises(sqlite3.ProgrammingError):
                connections[0].execute("SELECT 1")

    def test_validation_closes_connection_after_schema_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._candidate(directory)
            with sqlite3.connect(path) as db:
                db.execute("DROP TABLE acknowledgements")
            connections = []
            real_connect = sqlite3.connect

            def tracked_connect(*args, **kwargs):
                connection = real_connect(*args, **kwargs)
                connections.append(connection)
                return connection

            with patch("server.backup.sqlite3.connect", side_effect=tracked_connect):
                self.assertEqual(validate_restore_candidate(str(path)),
                                 (False, "RESTORE_CANDIDATE_SCHEMA_UNSUPPORTED"))
            self.assertEqual(len(connections), 1)
            with self.assertRaises(sqlite3.ProgrammingError):
                connections[0].execute("SELECT 1")

    def test_validation_supports_file_backed_journal_modes(self):
        for journal_mode in ("DELETE", "TRUNCATE", "PERSIST", "WAL"):
            with self.subTest(journal_mode=journal_mode):
                with tempfile.TemporaryDirectory() as directory:
                    path = self._candidate(directory)
                    with sqlite3.connect(path) as db:
                        actual = db.execute(
                            f"PRAGMA journal_mode={journal_mode}"
                        ).fetchone()[0].upper()
                    self.assertEqual(actual, journal_mode)
                    self.assertEqual(
                        validate_restore_candidate(str(path)),
                        (True, "RESTORE_CANDIDATE_VALIDATED"),
                    )


if __name__ == "__main__":
    unittest.main()
