import http.client
import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer

from server.http_server import MessengerHandler
from server.provider_audit_remote_anchor import _GENESIS_DIGEST, _record_from_checkpoint
from server.provider_audit_durable_anchor import SQLiteDurableAuditAnchor
from server.provider_audit_remote_service import ProviderAuditRemoteService


class ProviderAuditMessengerHTTPIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.anchor = SQLiteDurableAuditAnchor(
            os.path.join(self.directory.name, "remote-anchor.sqlite"))
        self.service = ProviderAuditRemoteService(
            self.anchor,
            authenticate_token=lambda token: "messenger-test-agent" if token == "valid-token" else None,
            authorize_principal=lambda principal: principal == "messenger-test-agent",
            max_body_bytes=256,
        )
        handler = type(
            "ConfiguredMessengerHandler",
            (MessengerHandler,),
            {"provider_audit_service": self.service},
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_address[1], timeout=3)

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.anchor.close()
        self.directory.cleanup()

    def _request(self, method, path, body=None, headers=None):
        self.connection.request(method, path, body=body, headers=headers or {})
        response = self.connection.getresponse()
        payload = response.read()
        return response.status, response.getheaders(), json.loads(payload) if payload else None

    def _record(self):
        checkpoint = {
            "audit_id": 100,
            "event_hash": "%064x" % 100,
            "created_at": 1.0,
            "signature": "%064x" % 1100,
        }
        return _record_from_checkpoint(checkpoint, None)

    def test_authenticated_latest_get_is_routed_through_messenger(self):
        status, headers, body = self._request(
            "GET", "/v1/audit-anchor/latest",
            headers={"Authorization": "Bearer valid-token"})
        self.assertEqual(status, 200)
        self.assertIsNone(body["record"])
        normalized = {key.lower(): value for key, value in headers}
        self.assertEqual(normalized["cache-control"], "no-store")
        self.assertEqual(normalized["x-content-type-options"], "nosniff")
        self.assertEqual(normalized["referrer-policy"], "no-referrer")

    def test_checkpoint_post_is_routed_and_persisted(self):
        payload = {"expected_sequence": 0, "record": self._record()}
        status, _, body = self._request(
            "POST", "/v1/audit-anchor/checkpoints",
            body=json.dumps(payload),
            headers={"Authorization": "Bearer valid-token",
                     "Content-Type": "application/json"})
        self.assertEqual(status, 201)
        self.assertFalse(body["replayed"])
        self.assertEqual(self.anchor.read_latest(), payload["record"])

    def test_invalid_bearer_is_rejected_by_service(self):
        status, _, body = self._request(
            "GET", "/v1/audit-anchor/latest",
            headers={"Authorization": "Bearer wrong-token"})
        self.assertEqual(status, 401)
        self.assertEqual(body["error"], "authentication_required")

    def test_wrong_method_is_rejected_by_service(self):
        status, _, body = self._request(
            "POST", "/v1/audit-anchor/latest", body=b"",
            headers={"Authorization": "Bearer valid-token",
                     "Content-Length": "0"})
        self.assertEqual(status, 405)
        self.assertEqual(body["error"], "method_not_allowed")

    def test_oversized_body_is_rejected_before_service_dispatch(self):
        status, _, body = self._request(
            "POST", "/v1/audit-anchor/checkpoints",
            body=b"x" * 257,
            headers={"Authorization": "Bearer valid-token",
                     "Content-Type": "application/json"})
        self.assertEqual(status, 413)
        self.assertEqual(body["error"], "request_body_too_large")

    def test_existing_health_route_remains_available(self):
        status, _, body = self._request("GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(body["service"], "ai-messenger-experimental")


class ProviderAuditMessengerHTTPDisabledTests(unittest.TestCase):
    def test_provider_audit_is_not_enabled_by_default(self):
        handler = type(
            "UnconfiguredMessengerHandler",
            (MessengerHandler,),
            {"provider_audit_service": None},
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=3)
        try:
            connection.request("GET", "/v1/audit-anchor/latest")
            response = connection.getresponse()
            body = json.loads(response.read())
            self.assertEqual(response.status, 404)
            self.assertEqual(body["error"], "not_found")
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
