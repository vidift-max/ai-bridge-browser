"""Explicit loopback-only server factory for the provider-audit HTTP adapter.

The returned server is bound but not started. Callers own its thread and
shutdown lifecycle. This standard-library server is for local/test use only.
"""
from http.server import ThreadingHTTPServer

from server.provider_audit_http_transport import make_provider_audit_http_handler


class _LoopbackProviderAuditHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = True


def create_provider_audit_http_server(service, host="127.0.0.1", port=0):
    """Create a bound, not-yet-started loopback HTTP server.

    The exact IPv4 loopback literal is required; wildcard, LAN, public, and
    hostname binds are deliberately rejected. Port zero asks the OS for an
    ephemeral port. The caller must start and stop the returned server.
    """
    if not callable(getattr(service, "handle", None)):
        raise ValueError("provider_audit_service_required")
    if host != "127.0.0.1":
        raise ValueError("loopback_host_required")
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("invalid_port")
    handler = make_provider_audit_http_handler(service)
    return _LoopbackProviderAuditHTTPServer((host, port), handler)
