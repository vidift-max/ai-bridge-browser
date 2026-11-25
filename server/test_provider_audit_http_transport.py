import json
import os
import socket
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from server.provider_audit_durable_anchor import SQLiteDurableAuditAnchor
from server.provider_audit_http_transport import make_provider_audit_http_handler
from server.provider_audit_remote_anchor import _GENESIS_DIGEST, _record_from_checkpoint
from server.provider_audit_remote_service import ProviderAuditRemoteService


class ProviderAuditHTTPTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.anchor = SQLiteDurableAuditAnchor(os.path.join(self.temp.name, "anchor.sqlite"))
        self.service = ProviderAuditRemoteService(
            self.anchor,
            authenticate_token=lambda token: "test-agent" if token == "transport-test-token" else None,
            authorize_principal=lambda principal: principal == "test-agent",
            max_body_bytes=8192,
        )
        handler = make_provider_audit_http_handler(self.service)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:%d" % self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temp.cleanup()

    def _request(self, method, path, payload=None, token="transport-test-token",
                 content_type="application/json", extra_headers=None):
        data = None if payload is None else (
            payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        )
        headers = {}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        if content_type is not None:
            headers["Content-Type"] = content_type
        headers.update(extra_headers or {})
        request = urllib.request.Request(
            self.base + path, data=data, headers=headers, method=method,
        )
        try:
            response = urllib.request.urlopen(request, timeout=3)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}, response.headers

    def _record(self):
        checkpoint = {
            "audit_id": 101,
            "event_hash": "%064x" % 101,
            "created_at": 1.0,
            "signature": "%064x" % 1101,
        }
        return _record_from_checkpoint(checkpoint, None)

    def test_get_latest_uses_real_http_transport(self):
        status, body, headers = self._request("GET", "/v1/audit-anchor/latest")
        self.assertEqual(status, 200)
        self.assertIsNone(body["record"])
        self.assertEqual(headers.get("Cache-Control"), "no-store")
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get_content_type(), "application/json")

    def test_post_appends_and_get_reads_same_record(self):
        record = self._record()
        status, body, _ = self._request(
            "POST", "/v1/audit-anchor/checkpoints",
            {"expected_sequence": 0, "record": record},
        )
        self.assertEqual(status, 201)
        self.assertFalse(body["replayed"])
        status, latest, _ = self._request("GET", "/v1/audit-anchor/latest")
        self.assertEqual(status, 200)
        self.assertEqual(latest["record"], record)

    def test_exact_post_retry_is_idempotent_over_http(self):
        record = self._record()
        payload = {"expected_sequence": 0, "record": record}
        self.assertEqual(self._request("POST", "/v1/audit-anchor/checkpoints", payload)[0], 201)
        status, body, _ = self._request("POST", "/v1/audit-anchor/checkpoints", payload)
        self.assertEqual(status, 200)
        self.assertTrue(body["replayed"])

    def test_missing_bearer_token_is_unauthorized(self):
        status, body, _ = self._request("GET", "/v1/audit-anchor/latest", token=None)
        self.assertEqual(status, 401)
        self.assertEqual(body["error"], "authentication_required")

    def test_invalid_bearer_token_is_unauthorized(self):
        status, _, _ = self._request("GET", "/v1/audit-anchor/latest", token="wrong")
        self.assertEqual(status, 401)

    def test_unknown_path_returns_not_found(self):
        status, body, _ = self._request("GET", "/not-an-endpoint")
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")

    def test_put_method_is_rejected(self):
        status, body, headers = self._request("PUT", "/v1/audit-anchor/latest")
        self.assertEqual(status, 405)
        self.assertEqual(body["error"], "method_not_allowed")

    def test_post_requires_json_content_type(self):
        status, body, _ = self._request(
            "POST", "/v1/audit-anchor/checkpoints", b"{}",
            content_type="text/plain",
        )
        self.assertEqual(status, 415)
        self.assertEqual(body["error"], "content_type_required")

    def test_malformed_json_returns_400(self):
        status, body, _ = self._request(
            "POST", "/v1/audit-anchor/checkpoints", b"{",
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_json")

    def test_body_larger_than_limit_is_rejected_before_service(self):
        status, body, _ = self._request(
            "POST", "/v1/audit-anchor/checkpoints", b"x" * 8193,
        )
        self.assertEqual(status, 413)
        self.assertEqual(body["error"], "request_body_too_large")

    def test_response_contains_no_store_and_no_sniff_headers(self):
        _, _, headers = self._request("GET", "/v1/audit-anchor/latest")
        self.assertEqual(headers.get("Cache-Control"), "no-store")
        self.assertEqual(headers.get("Pragma"), "no-cache")
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("Referrer-Policy"), "no-referrer")

    def test_missing_content_length_is_rejected_for_post(self):
        connection = socket.create_connection(self.server.server_address, timeout=3)
        try:
            request = (
                "POST /v1/audit-anchor/checkpoints HTTP/1.1\r\n"
                "Host: 127.0.0.1\r\n"
                "Authorization: Bearer transport-test-token\r\n"
                "Content-Type: application/json\r\n"
                "Connection: close\r\n\r\n"
            )
            connection.sendall(request.encode("ascii"))
            chunks = []
            while True:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            response = b"".join(chunks).decode("iso-8859-1")
            self.assertIn(" 411 ", response.split("\r\n", 1)[0])
            self.assertIn("content_length_required", response)
        finally:
            connection.close()

    def test_rate_limit_is_enforced_through_transport(self):
        limited = ProviderAuditRemoteService(
            self.anchor,
            authenticate_token=lambda token: "limited" if token == "transport-test-token" else None,
            authorize_principal=lambda principal: principal == "limited",
            requests_per_window=1,
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_provider_audit_http_handler(limited))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:%d" % server.server_address[1]
        try:
            request = urllib.request.Request(base + "/v1/audit-anchor/latest",
                headers={"Authorization": "Bearer transport-test-token"})
            with urllib.request.urlopen(request, timeout=3) as response:
                self.assertEqual(response.status, 200)
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request, timeout=3)
            self.assertEqual(caught.exception.code, 429)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
