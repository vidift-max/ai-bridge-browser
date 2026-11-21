import unittest

from server.audit import AuditLog
from server.sqlite_store import SQLiteMessengerStore


class Mission16ReliabilityTest(unittest.TestCase):
    def test_audit_redacts_secret_subject(self):
        log = AuditLog()
        event = log.record("TEST", "Bearer super-secret", metadata={"token": "secret", "safe": "ok"})
        self.assertEqual(event.subject, "[redacted]")
        self.assertNotIn("secret", str(event.metadata))
        self.assertEqual(event.metadata["safe"], "ok")

    def test_atomic_message_persistence_survives_restart(self):
        store = SQLiteMessengerStore(":memory:")
        store.save_message_with_idempotency(("m1","room","AI-A",("AI-B",),"body","req-1",1))
        self.assertEqual(store.find_idempotency("AI-A","req-1"), "m1")
        self.assertEqual(store.load_messages()[0]["message_id"], "m1")
        store.close()

    def test_atomic_duplicate_rolls_back(self):
        store = SQLiteMessengerStore(":memory:")
        store.save_message_with_idempotency(("m1","room","AI-A",("AI-B",),"body","req-1",1))
        with self.assertRaises(Exception):
            store.save_message_with_idempotency(("m2","room","AI-A",("AI-B",),"body2","req-1",2))
        rows = store.load_messages()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["message_id"], "m1")
        store.close()


if __name__ == "__main__":
    unittest.main()
