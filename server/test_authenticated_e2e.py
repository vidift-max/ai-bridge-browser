import tempfile
import unittest

from server.auth import Authenticator
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore


class AuthenticatedE2ETest(unittest.TestCase):
    def test_ai_a_to_ai_b_message_ack_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = directory + "/messenger.sqlite"
            tokens = {"token-a": "AI-A", "token-b": "AI-B"}
            auth = Authenticator(tokens)
            store = SQLiteMessengerStore(path)
            backend = MessengerBackend(tokens, {"room": {"AI-A", "AI-B"}}, store)

            self.assertEqual(auth.authenticate("token-a").ai_id, "AI-A")
            message = backend.submit("token-a", "m-1", "room", ["AI-B"], "hello", "req-1")
            self.assertEqual(backend.pending("token-b", "room")[0].message_id, "m-1")
            backend.acknowledge("token-b", "m-1")
            backend.close()

            restarted = MessengerBackend(tokens, {"room": {"AI-A", "AI-B"}}, SQLiteMessengerStore(path))
            self.assertEqual(restarted.pending("token-b", "room"), [])
            self.assertEqual(restarted.pending("token-a", "room"), [])
            restarted.close()

    def test_revoked_sender_cannot_submit(self):
        tokens = {"token-a": "AI-A", "token-b": "AI-B"}
        auth = Authenticator(tokens)
        auth.revoke("token-a")
        backend = MessengerBackend(tokens, {"room": {"AI-A", "AI-B"}})
        with self.assertRaises(PermissionError):
            auth.authenticate("token-a")
        with self.assertRaises(PermissionError):
            backend.submit("token-a", "m-2", "room", ["AI-B"], "blocked", "req-2")
        backend.close()


if __name__ == "__main__":
    unittest.main()
