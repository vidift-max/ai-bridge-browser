import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_first_contact as runner


class Mission110ExecutionSafetyTest(unittest.TestCase):
    def test_cli_requires_execute_flag_before_any_contact(self):
        with patch.object(sys, "argv", ["verify_first_contact.py", "https://stage.example", "room"]), \
             patch.dict(os.environ, {"MESSENGER_FIRST_CONTACT_EXECUTE": "true"}), \
             patch.object(runner, "run_first_contact") as execute:
            self.assertEqual(runner.main(), 2)
            execute.assert_not_called()

    def test_cli_requires_explicit_environment_gate(self):
        with patch.object(sys, "argv", ["verify_first_contact.py", "--execute", "https://stage.example", "room"]), \
             patch.dict(os.environ, {"MESSENGER_FIRST_CONTACT_EXECUTE": "false"}), \
             patch.object(runner, "run_first_contact") as execute:
            self.assertEqual(runner.main(), 2)
            execute.assert_not_called()

    def test_cli_executes_only_when_both_gates_are_present(self):
        with patch.object(sys, "argv", ["verify_first_contact.py", "--execute", "https://stage.example", "room"]), \
             patch.dict(os.environ, {"MESSENGER_FIRST_CONTACT_EXECUTE": "true",
                                     "MESSENGER_TOKEN_AI_A": "secret-a",
                                     "MESSENGER_TOKEN_AI_B": "secret-b"}), \
             patch.object(runner, "run_first_contact", return_value={"result": "PASS"}) as execute:
            self.assertEqual(runner.main(), 0)
            execute.assert_called_once_with("https://stage.example", "room", "secret-a", "secret-b")

    def test_redirect_is_not_followed_and_bearer_is_not_forwarded(self):
        destination_hits = []

        class DestinationHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                destination_hits.append(self.headers.get("Authorization"))
                self.send_response(200)
                self.end_headers()
            def log_message(self, *args):
                pass

        destination = HTTPServer(("127.0.0.1", 0), DestinationHandler)
        destination_thread = threading.Thread(target=destination.serve_forever, daemon=True)
        destination_thread.start()

        class RedirectHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{destination.server_port}/capture")
                self.end_headers()
            def log_message(self, *args):
                pass

        redirect = HTTPServer(("127.0.0.1", 0), RedirectHandler)
        redirect_thread = threading.Thread(target=redirect.serve_forever, daemon=True)
        redirect_thread.start()
        try:
            status, body = runner.request_json(
                f"http://127.0.0.1:{redirect.server_port}", "/start", "sensitive-token")
            self.assertEqual(status, 302)
            self.assertEqual(body, {"error": "http_error"})
            self.assertEqual(destination_hits, [])
        finally:
            redirect.shutdown()
            destination.shutdown()
            redirect.server_close()
            destination.server_close()
            redirect_thread.join(timeout=2)
            destination_thread.join(timeout=2)

    def test_redirect_error_does_not_echo_secret_or_response_body(self):
        status, body = runner._decode(b'{"error":"sensitive-token"}'), None
        self.assertEqual(status, {"error": "sensitive-token"})
        self.assertIsNone(body)


if __name__ == "__main__":
    unittest.main()
