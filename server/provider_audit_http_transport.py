"""Bounded stdlib HTTP transport for ProviderAuditRemoteService.

This factory creates an in-process HTTP handler. It does not bind a socket,
start a listener, or alter the application's production server by itself.
Deployments must provide TLS and lifecycle management at their boundary.
"""
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlsplit


def make_provider_audit_http_handler(service):
    """Return a BaseHTTPRequestHandler class bound to one service instance."""
    if not callable(getattr(service, "handle", None)):
        raise ValueError("provider_audit_service_required")

    class ProviderAuditHTTPHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def _respond(self, status, payload):
            try:
                body = json.dumps(
                    payload, ensure_ascii=False, separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8")
            except (TypeError, ValueError):
                status = 503
                body = b'{"error":"response_serialization_failed"}'
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Pragma", "no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _request_body(self):
            if self.headers.get("Transfer-Encoding") is not None:
                return None, (400, {"error": "transfer_encoding_not_supported"})
            raw_length = self.headers.get("Content-Length")
            if raw_length is None:
                if self.command == "GET":
                    return b"", None
                return None, (411, {"error": "content_length_required"})
            if not raw_length.isascii() or not raw_length.isdecimal():
                return None, (400, {"error": "invalid_content_length"})
            # Bound before reading from the socket; no unbounded body allocation.
            length = int(raw_length)
            if length > service.max_body_bytes:
                return None, (413, {"error": "request_body_too_large"})
            if length == 0:
                return b"", None
            body = self.rfile.read(length)
            if len(body) != length:
                return None, (400, {"error": "incomplete_request_body"})
            return body, None

        def _dispatch(self):
            path = urlsplit(self.path).path
            if path not in (
                "/v1/audit-anchor/latest",
                "/v1/audit-anchor/checkpoints",
            ):
                self._respond(404, {"error": "not_found"})
                return
            body, error = self._request_body()
            if error is not None:
                self._respond(*error)
                return
            headers = {
                "Authorization": self.headers.get("Authorization", ""),
                "Content-Type": self.headers.get("Content-Type", ""),
            }
            try:
                status, payload = service.handle(
                    self.command, path, headers=headers, body=body,
                )
            except Exception:
                status, payload = 503, {"error": "service_unavailable"}
            self._respond(status, payload)

        def do_GET(self):
            self._dispatch()

        def do_POST(self):
            self._dispatch()

        def do_PUT(self):
            self._respond(405, {"error": "method_not_allowed"})

        def do_PATCH(self):
            self._respond(405, {"error": "method_not_allowed"})

        def do_DELETE(self):
            self._respond(405, {"error": "method_not_allowed"})

        def do_OPTIONS(self):
            self.send_response(405)
            self.send_header("Allow", "GET, POST")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_args):
            # BaseHTTPRequestHandler's default log includes request targets.
            # Suppress access logging here to avoid accidental credential leakage.
            return

    return ProviderAuditHTTPHandler
