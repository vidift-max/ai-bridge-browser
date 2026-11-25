"""Bounded stdlib HTTP transport for ProviderAuditRemoteService.

This factory creates an in-process HTTP handler. It does not bind a socket,
start a listener, or alter the application's production server by itself.
Deployments must provide TLS and lifecycle management at their boundary.
"""
import json
from http.server import BaseHTTPRequestHandler
from server.provider_audit_http_dispatch import (
    dispatch_provider_audit_request,
    read_provider_audit_request_body,
)


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
            if self.close_connection:
                self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)

        def _request_body(self):
            return read_provider_audit_request_body(
                self.headers, self.command, self.rfile, service.max_body_bytes,
            )

        def _dispatch(self):
            body, error = self._request_body()
            if error is not None:
                self.close_connection = True
                self._respond(*error)
                return
            headers = {
                "Authorization": self.headers.get("Authorization", ""),
                "Content-Type": self.headers.get("Content-Type", ""),
            }
            status, payload = dispatch_provider_audit_request(
                service, self.command, self.path, headers, body,
            )
            self._respond(status, payload)

        def do_GET(self):
            self._dispatch()

        def do_POST(self):
            self._dispatch()

        def _method_not_allowed(self):
            self.close_connection = True
            self._respond(405, {"error": "method_not_allowed"})

        def do_PUT(self):
            self._method_not_allowed()

        def do_PATCH(self):
            self._method_not_allowed()

        def do_DELETE(self):
            self._method_not_allowed()

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
