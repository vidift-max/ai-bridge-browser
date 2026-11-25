"""Authenticated HTTP service contract for a provider-audit remote anchor.

The service is transport-ready but deliberately not mounted in the application
server. Authentication and authorization are injected; this module never stores
or provisions credentials. Use TLS at the deployment boundary.
"""
import json
import re
import threading
import time

from server.provider_audit_remote_anchor import _validate_record


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_constant(_value):
    raise ValueError("invalid_json_constant")


class ProviderAuditRemoteService:
    """Small HTTP request handler contract around an append-only anchor adapter."""

    def __init__(self, anchor, authenticate_token, authorize_principal=None,
                 max_body_bytes=8192, requests_per_window=60, window_seconds=60,
                 clock=time.monotonic):
        if not callable(authenticate_token):
            raise ValueError("authenticate_token_required")
        if authorize_principal is not None and not callable(authorize_principal):
            raise ValueError("authorize_principal_invalid")
        if not callable(clock):
            raise ValueError("clock_invalid")
        if type(max_body_bytes) is not int or not 256 <= max_body_bytes <= 65536:
            raise ValueError("invalid_max_body_bytes")
        if type(requests_per_window) is not int or requests_per_window < 1:
            raise ValueError("invalid_rate_limit")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)) or window_seconds <= 0:
            raise ValueError("invalid_rate_window")
        self.anchor = anchor
        self.authenticate_token = authenticate_token
        self.authorize_principal = authorize_principal or (lambda _principal: False)
        self.max_body_bytes = max_body_bytes
        self.requests_per_window = requests_per_window
        self.window_seconds = float(window_seconds)
        self.clock = clock
        self._lock = threading.Lock()
        self._requests = {}

    def _authenticate(self, headers):
        value = headers.get("Authorization", "")
        if not isinstance(value, str) or not value.startswith("Bearer "):
            return None, 401
        token = value[7:]
        if not token or len(token) > 4096 or not token.isascii():
            return None, 401
        try:
            principal = self.authenticate_token(token)
        except Exception:
            return None, 401
        if not isinstance(principal, str) or not principal or len(principal) > 128:
            return None, 401
        try:
            if self.authorize_principal(principal) is not True:
                return None, 403
        except Exception:
            return None, 403
        return principal, None

    def _allow_request(self, principal):
        now = self.clock()
        with self._lock:
            recent = [stamp for stamp in self._requests.get(principal, [])
                      if now - stamp < self.window_seconds]
            if len(recent) >= self.requests_per_window:
                self._requests[principal] = recent
                return False
            recent.append(now)
            self._requests[principal] = recent
            return True

    def handle(self, method, path, headers=None, body=b""):
        headers = headers or {}
        body = body or b""
        if path not in ("/v1/audit-anchor/latest", "/v1/audit-anchor/checkpoints"):
            return 404, {"error": "not_found"}
        principal, auth_error = self._authenticate(headers)
        if auth_error:
            return auth_error, {"error": "authentication_required" if auth_error == 401 else "forbidden"}
        if not self._allow_request(principal):
            return 429, {"error": "rate_limit_exceeded"}
        if method == "GET" and path == "/v1/audit-anchor/latest":
            if body:
                return 400, {"error": "unexpected_request_body"}
            try:
                return 200, {"record": self.anchor.read_latest()}
            except Exception:
                return 503, {"error": "anchor_unavailable"}
        if method != "POST" or path != "/v1/audit-anchor/checkpoints":
            return 405, {"error": "method_not_allowed"}
        if headers.get("Content-Type", "").split(";", 1)[0].lower() != "application/json":
            return 415, {"error": "content_type_required"}
        if len(body) < 1 or len(body) > self.max_body_bytes:
            return 413, {"error": "request_body_size_invalid"}
        try:
            payload = json.loads(body.decode("utf-8"), object_pairs_hook=_unique_object,
                                 parse_constant=_reject_constant)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return 400, {"error": "invalid_json"}
        if not isinstance(payload, dict) or set(payload) != {"expected_sequence", "record"}:
            return 400, {"error": "invalid_request_schema"}
        expected = payload["expected_sequence"]
        record = payload["record"]
        if type(expected) is not int or expected < 0:
            return 400, {"error": "invalid_expected_sequence"}
        try:
            _validate_record(record)
        except (TypeError, ValueError):
            return 400, {"error": "invalid_anchor_record"}
        try:
            latest = self.anchor.read_latest()
            # Safe replay: an exact retry of the latest committed record is idempotent.
            if latest == record:
                return 200, {"record": latest, "replayed": True}
            stored = self.anchor.append_checkpoint(expected, record)
            return 201, {"record": stored, "replayed": False}
        except ValueError as exc:
            reason = str(exc)
            if reason in ("remote_anchor_sequence_conflict", "remote_anchor_sequence_invalid",
                          "remote_anchor_chain_conflict", "remote_anchor_audit_id_not_monotonic"):
                return 409, {"error": reason}
            return 400, {"error": "invalid_anchor_record"}
        except Exception:
            return 503, {"error": "anchor_unavailable"}


from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class ProviderAuditAnchorHTTPHandler(BaseHTTPRequestHandler):
    """Minimal HTTP/1.1 adapter; service owns auth, policy, validation and storage."""

    service = None
    server_version = "AI-BRIDGE-AUDIT/1"
    sys_version = ""

    def log_message(self, _format, *_args):
        # Never log Authorization headers, request bodies, or checkpoint material.
        return

    def _dispatch(self, method):
        if self.service is None:
            self._write_json(503, {"error": "service_unavailable"})
            return
        try:
            raw_length = self.headers.get("Content-Length", "0")
            if not raw_length.isascii() or not raw_length.isdecimal():
                self._write_json(400, {"error": "invalid_content_length"})
                return
            length = int(raw_length)
            if length > self.service.max_body_bytes:
                body = b"x" * (self.service.max_body_bytes + 1)
            else:
                body = self.rfile.read(length) if length else b""
            status, payload = self.service.handle(
                method, self.path, dict(self.headers.items()), body)
            self._write_json(status, payload)
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception:
            self._write_json(503, {"error": "service_unavailable"})

    def _write_json(self, status, payload):
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_PUT(self):
        self._dispatch("PUT")

    def do_PATCH(self):
        self._dispatch("PATCH")

    def do_DELETE(self):
        self._dispatch("DELETE")


def create_provider_audit_anchor_http_server(service, host="127.0.0.1", port=0):
    """Create an opt-in loopback-first server; callers explicitly choose exposure."""
    if not isinstance(service, ProviderAuditRemoteService):
        raise ValueError("provider_audit_service_required")
    if host != "127.0.0.1":
        raise ValueError("non_loopback_bind_requires_explicit_deployment_adapter")
    handler = type("BoundProviderAuditAnchorHTTPHandler",
                   (ProviderAuditAnchorHTTPHandler,), {"service": service})
    return ThreadingHTTPServer((host, port), handler)
