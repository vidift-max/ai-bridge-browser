import os
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_first_contact import run_first_contact
from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.sqlite_store import SQLiteMessengerStore
from server.audio_blob_store import AudioBlobStore
from server.operational_runtime import OperationalRuntime


class Mission113FirstContactLocalHttpE2ETest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        self.tmp.close()
        self.tokens = {"token-ai-01": "AI-01", "token-ai-02": "AI-02"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(self.tmp.name)
        self.backend = MessengerBackend(
            self.tokens, {"mission-113-room": {"AI-01", "AI-02"}},
            self.store, authenticator=self.auth)
        MessengerHandler.backend = self.backend
        from server.rate_limit import SlidingWindowRateLimiter
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter()
        MessengerHandler.authenticator = self.auth
        from server.voice_room_control import VoiceRoomControl
        MessengerHandler.voice_control = VoiceRoomControl({"AI-01"}, store=self.store)
        MessengerHandler.operational = OperationalRuntime()
        self.audio_dir = tempfile.TemporaryDirectory()
        MessengerHandler.audio_store = AudioBlobStore(self.audio_dir.name)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MessengerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.backend.close()
        MessengerHandler.operational = None
        MessengerHandler.audio_store = None
        MessengerHandler.voice_control = None
        self.audio_dir.cleanup()
        os.unlink(self.tmp.name)

    def test_real_local_http_identity_send_long_poll_ack_and_pending_removal(self):
        base_url = f"http://127.0.0.1:{self.server.server_port}"
        result = run_first_contact(
            base_url, "mission-113-room", "token-ai-01", "token-ai-02",
            operation_id="mission-113-local-http-proof-001")
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["sender"], "AI-01")
        self.assertEqual(result["recipient"], "AI-02")
        self.assertTrue(result["received"])
        self.assertTrue(result["acknowledged"])
        self.assertTrue(result["removedFromPending"])
        events = [event.event_type for event in self.auth.audit_log.events()]
        self.assertIn("MESSAGE_SUBMITTED", events)
        self.assertIn("MESSAGE_ACKNOWLEDGED", events)


if __name__ == "__main__":
    unittest.main()
