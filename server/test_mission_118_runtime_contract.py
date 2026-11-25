import json
import os
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from server.auth import Authenticator
from server.http_server import MessengerHandler
from server.messenger_backend import MessengerBackend
from server.operational_runtime import OperationalRuntime
from server.sqlite_store import SQLiteMessengerStore
from scripts.verify_first_contact import run_first_contact, request_json
from scripts.verify_staging_http import normalize_base_url


class Mission118RuntimeContractTest(unittest.TestCase):
    def setUp(self):
        self.tokens = {"synthetic-ai01-token": "AI-01", "synthetic-ai02-token": "AI-02"}
        self.auth = Authenticator(self.tokens)
        self.store = SQLiteMessengerStore(":memory:")
        self.backend = MessengerBackend(
            self.tokens, {"default": {"AI-01", "AI-02"}},
            self.store, authenticator=self.auth)
        MessengerHandler.backend = self.backend
        MessengerHandler.authenticator = self.auth
        MessengerHandler.operational = OperationalRuntime()
        from server.rate_limit import SlidingWindowRateLimiter
        MessengerHandler.rate_limiter = SlidingWindowRateLimiter()
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

    def request(self, method, path, token=None, payload=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=4)
        headers = {}
        if token:
            headers["Authorization"] = "Bearer " + token
        body = None
        if payload is not None:
            body = json.dumps(payload)
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, data

    def test_ephemeral_readyz_checks_live_database_connection(self):
        env = {
            "MESSENGER_TOKEN_AI_A": "synthetic-ai01-token",
            "MESSENGER_TOKEN_AI_B": "synthetic-ai02-token",
            "MESSENGER_AI_ID_A": "AI-01",
            "MESSENGER_AI_ID_B": "AI-02",
            "MESSENGER_ENVIRONMENT": "staging",
            "MESSENGER_ALLOW_EPHEMERAL_STAGING": "true",
            "MESSENGER_STORAGE_MODE": "ephemeral",
            "MESSENGER_DB_PATH": ":memory:",
        }
        with patch.dict(os.environ, env, clear=False):
            status, body = self.request("GET", "/readyz")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"status": "ready", "storageMode": "ephemeral"})

    def test_ephemeral_storage_without_live_connection_fails_closed(self):
        ok, code = MessengerHandler.operational.check_storage(":memory:")
        self.assertFalse(ok)
        self.assertEqual(code, "STORAGE_CONNECTION_REQUIRED")

    def test_runtime_default_conversation_supports_identity_send_long_poll_ack(self):
        transport = lambda _base, path, token, method="GET", payload=None: request_json(
            f"http://127.0.0.1:{self.server.server_port}", path, token, method, payload)
        result = run_first_contact(
            "https://staging.example", "default",
            "synthetic-ai01-token", "synthetic-ai02-token",
            request=transport, operation_id="mission-118-local-runtime-001")
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["sender"], "AI-01")
        self.assertEqual(result["recipient"], "AI-02")
        self.assertTrue(result["received"])
        self.assertTrue(result["acknowledged"])
        self.assertTrue(result["removedFromPending"])

    def test_blueprint_start_command_binds_render_port_and_runtime_entrypoint(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        blueprint = (root / "render.staging.yaml").read_text(encoding="utf-8")
        self.assertIn("from server.http_server import serve", blueprint)
        self.assertIn("os.environ.get('PORT','10000')", blueprint)
        self.assertIn("healthCheckPath: /healthz", blueprint)
        self.assertEqual(normalize_base_url("https://staging.example/"),
                         "https://staging.example")


if __name__ == "__main__":
    unittest.main()
