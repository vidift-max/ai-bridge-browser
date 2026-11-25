# Mission 167 — Provider Audit Messenger HTTP Integration

## Scope

This change adds opt-in routes for the Provider Audit remote-anchor service to the existing Messenger HTTP handler:

- `GET /v1/audit-anchor/latest`
- `POST /v1/audit-anchor/checkpoints`

The service is injected through `MessengerHandler.provider_audit_service`. Its default is `None`; when it is not explicitly configured, these routes return 404. The Messenger bootstrap does not create an anchor, load credentials, or enable this integration automatically.

## Shared transport boundary

`server/provider_audit_http_dispatch.py` contains the shared bounded Content-Length reader and service dispatch used by both the standalone Provider Audit HTTP adapter and the Messenger handler. It rejects Transfer-Encoding, invalid or missing framing, oversized bodies, and incomplete reads before service dispatch. Authentication, authorization, method/path semantics, and per-principal rate limiting remain owned by `ProviderAuditRemoteService`.

Responses use JSON with Content-Length, no-store/no-cache, nosniff, and no-referrer headers. Existing Messenger endpoints remain on their existing handlers.

## Verification

The dedicated Python 3.12 workflow compiles the server and runs the Messenger integration tests together with the existing Provider Audit, Messenger, durable-anchor, replay, and recovery suites. The integration tests use an in-process IPv4 loopback server, a temporary SQLite anchor, and test-only bearer authentication.

## Security and deployment boundary

This is code-level integration and loopback test coverage only. It does not configure `MessengerHandler.provider_audit_service` in `serve()`, start a new listener, provision credentials, create a remote trust domain, configure TLS, expose a public endpoint, or deploy infrastructure. The existing standalone stdlib HTTP server remains local/test-only. No paid provider calls, device activation, browser-session access, or AI-to-AI communication are performed.
