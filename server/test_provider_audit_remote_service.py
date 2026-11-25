import json
import os
import tempfile
import unittest

from server.provider_audit_remote_anchor import _GENESIS_DIGEST, _record_from_checkpoint
from server.provider_audit_durable_anchor import SQLiteDurableAuditAnchor
from server.provider_audit_remote_service import ProviderAuditRemoteService


class ProviderAuditRemoteServiceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.anchor = SQLiteDurableAuditAnchor(os.path.join(self.directory.name, "anchor.sqlite"))
        self.service = ProviderAuditRemoteService(
            self.anchor,
            authenticate_token=lambda token: "service-agent" if token == "test-token" else None,
            authorize_principal=lambda principal: principal == "service-agent",
        )
        self.headers = {"Authorization": "Bearer test-token"}

    def tearDown(self):
        self.directory.cleanup()

    def _record(self, sequence=1, audit_id=100, previous=_GENESIS_DIGEST):
        checkpoint = {
            "audit_id": audit_id,
            "event_hash": "%064x" % audit_id,
            "created_at": float(sequence),
            "signature": "%064x" % (audit_id + 1000),
        }
        previous_record = None
        if sequence > 1:
            previous_record = {"sequence": sequence - 1, "record_digest": previous}
        return _record_from_checkpoint(checkpoint, previous_record)

    def _post(self, payload, headers=None):
        return self.service.handle(
            "POST", "/v1/audit-anchor/checkpoints",
            headers=headers or {**self.headers, "Content-Type": "application/json"},
            body=json.dumps(payload).encode("utf-8"),
        )

    def test_latest_requires_authentication(self):
        status, body = self.service.handle("GET", "/v1/audit-anchor/latest")
        self.assertEqual(status, 401)
        self.assertEqual(body["error"], "authentication_required")

    def test_invalid_token_is_rejected(self):
        status, _ = self.service.handle(
            "GET", "/v1/audit-anchor/latest", {"Authorization": "Bearer wrong"})
        self.assertEqual(status, 401)

    def test_authorization_denial_is_forbidden(self):
        service = ProviderAuditRemoteService(
            self.anchor, lambda _token: "unapproved", lambda _principal: False)
        status, _ = service.handle("GET", "/v1/audit-anchor/latest", self.headers)
        self.assertEqual(status, 403)

    def test_latest_returns_empty_record_for_empty_anchor(self):
        status, body = self.service.handle("GET", "/v1/audit-anchor/latest", self.headers)
        self.assertEqual(status, 200)
        self.assertIsNone(body["record"])

    def test_post_appends_checkpoint_and_get_reads_it(self):
        record = self._record()
        status, body = self._post({"expected_sequence": 0, "record": record})
        self.assertEqual(status, 201)
        self.assertFalse(body["replayed"])
        read_status, read_body = self.service.handle(
            "GET", "/v1/audit-anchor/latest", self.headers)
        self.assertEqual(read_status, 200)
        self.assertEqual(read_body["record"], record)

    def test_exact_latest_retry_is_idempotent(self):
        record = self._record()
        self.assertEqual(self._post({"expected_sequence": 0, "record": record})[0], 201)
        status, body = self._post({"expected_sequence": 0, "record": record})
        self.assertEqual(status, 200)
        self.assertTrue(body["replayed"])
        self.assertEqual(self.anchor.verify_history()["records_checked"], 1)

    def test_stale_sequence_conflict_is_http_409(self):
        first = self._record()
        self._post({"expected_sequence": 0, "record": first})
        second = self._record(2, 200, first["record_digest"])
        status, body = self._post({"expected_sequence": 0, "record": second})
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "remote_anchor_sequence_conflict")

    def test_invalid_record_is_rejected(self):
        status, body = self._post({"expected_sequence": 0, "record": {"sequence": 1}})
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_anchor_record")

    def test_duplicate_json_keys_are_rejected(self):
        raw = b'{"expected_sequence":0,"expected_sequence":1,"record":{}}'
        status, body = self.service.handle(
            "POST", "/v1/audit-anchor/checkpoints",
            {**self.headers, "Content-Type": "application/json"}, raw)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_json")

    def test_content_type_is_required(self):
        status, body = self.service.handle(
            "POST", "/v1/audit-anchor/checkpoints", self.headers, b"{}")
        self.assertEqual(status, 415)
        self.assertEqual(body["error"], "content_type_required")

    def test_oversized_body_is_rejected(self):
        status, body = self.service.handle(
            "POST", "/v1/audit-anchor/checkpoints",
            {**self.headers, "Content-Type": "application/json"}, b"x" * 9000)
        self.assertEqual(status, 413)
        self.assertEqual(body["error"], "request_body_size_invalid")

    def test_wrong_method_is_rejected(self):
        status, body = self.service.handle(
            "DELETE", "/v1/audit-anchor/latest", self.headers)
        self.assertEqual(status, 405)
        self.assertEqual(body["error"], "method_not_allowed")

    def test_unknown_path_is_not_found(self):
        status, body = self.service.handle("GET", "/unknown", self.headers)
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")

    def test_rate_limit_is_scoped_to_authenticated_principal(self):
        service = ProviderAuditRemoteService(
            self.anchor, lambda _token: "service-agent",
            requests_per_window=1, window_seconds=60)
        self.assertEqual(service.handle("GET", "/v1/audit-anchor/latest", self.headers)[0], 200)
        self.assertEqual(service.handle("GET", "/v1/audit-anchor/latest", self.headers)[0], 429)

    def test_anchor_failure_fails_closed(self):
        class BrokenAnchor:
            def read_latest(self):
                raise OSError("offline")
        service = ProviderAuditRemoteService(BrokenAnchor(), lambda _token: "service-agent")
        status, body = service.handle("GET", "/v1/audit-anchor/latest", self.headers)
        self.assertEqual(status, 503)
        self.assertEqual(body["error"], "anchor_unavailable")


if __name__ == "__main__":
    unittest.main()
