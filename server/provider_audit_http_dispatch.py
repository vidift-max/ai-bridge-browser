"""Shared bounded request parsing and dispatch for Provider Audit HTTP routes."""
from urllib.parse import urlsplit

PROVIDER_AUDIT_PATHS = frozenset({
    "/v1/audit-anchor/latest",
    "/v1/audit-anchor/checkpoints",
})


def read_provider_audit_request_body(headers, method, stream, max_body_bytes):
    """Read only a validated, bounded Content-Length framed request body."""
    if headers.get("Transfer-Encoding") is not None:
        return None, (400, {"error": "transfer_encoding_not_supported"})
    raw_length = headers.get("Content-Length")
    if raw_length is None:
        if method == "GET":
            return b"", None
        return None, (411, {"error": "content_length_required"})
    if (not raw_length.isascii() or not raw_length.isdecimal()
            or len(raw_length) > 10):
        return None, (400, {"error": "invalid_content_length"})
    length = int(raw_length)
    if length > max_body_bytes:
        return None, (413, {"error": "request_body_too_large"})
    if length == 0:
        return b"", None
    body = stream.read(length)
    if len(body) != length:
        return None, (400, {"error": "incomplete_request_body"})
    return body, None


def dispatch_provider_audit_request(service, method, target, headers, body):
    """Delegate an already-framed request to the authenticated service contract."""
    path = urlsplit(target).path
    if path not in PROVIDER_AUDIT_PATHS:
        return 404, {"error": "not_found"}
    try:
        return service.handle(method, path, headers=headers, body=body)
    except Exception:
        return 503, {"error": "service_unavailable"}
