import tempfile
import unittest

from server.auth import Authenticator
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore


class HttpE2ERecoveryTest(unittest.TestCase):
    def test_message_and_ack_survive_backend_restart(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False); tmp.close()
        tokens = {"token-a": "AI-A", "token-b": "AI-B"}
        auth = Authenticator(tokens)
        store = SQLiteMessengerStore(tmp.name)
        backend = MessengerBackend(tokens, {"room": {"AI-A", "AI-B"}}, store, authenticator=auth)
        backend.submit("token-a", "m-restart", "room", ["AI-B"], "persist me", "req-restart")
        backend.close()

        auth2 = Authenticator(tokens)
        store2 = SQLiteMessengerStore(tmp.name)
        backend2 = MessengerBackend(tokens, {"room": {"AI-A", "AI-B"}}, store2, authenticator=auth2)
        pending = backend2.pending("token-b", "room")
        self.assertEqual([m.message_id for m in pending], ["m-restart"])
        backend2.acknowledge("token-b", "m-restart")
        backend2.close()

        auth3 = Authenticator(tokens)
        store3 = SQLiteMessengerStore(tmp.name)
        backend3 = MessengerBackend(tokens, {"room": {"AI-A", "AI-B"}}, store3, authenticator=auth3)
        self.assertEqual(backend3.pending("token-b", "room"), [])
        backend3.close()


if __name__ == "__main__":
    unittest.main()
