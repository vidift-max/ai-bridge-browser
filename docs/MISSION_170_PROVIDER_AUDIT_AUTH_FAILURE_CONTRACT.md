# Mission 170 — Provider Audit Authentication and Failure Contract

## Scope

Strengthen executable tests around the existing remote service's fail-closed
security boundary. This mission does not change production bootstrap, enable
Provider Audit routes, create external infrastructure, or provision secrets.

## Required behavior

- An authentication callback exception or invalid principal is HTTP 401.
- An authorization callback exception or any value other than literal boolean
  `True` is HTTP 403.
- A durable-anchor append failure is HTTP 503 and does not report success.
- Existing successful authentication, authorization, read/write, idempotency,
  rate-limit, and Messenger default-disabled behavior remain covered by their
  existing tests.

## Operational boundary

The service is still not mounted by `serve()`; the Messenger route remains
disabled unless a handler instance is explicitly composed with a service.
The loopback HTTP server factory is a local/test-only helper, not a production
TLS endpoint. The SQLite anchor remains a reference adapter and not an
independent trust domain.

Before any production activation, a separate approved mission must specify
the independently administered anchor service, TLS termination and trust,
secret issuance/rotation/revocation, principal-to-AI authorization mapping,
backup and restore evidence, monitoring, incident response, and rollback.
No production endpoint, credentials, external network, paid API, or device is
used by this mission.

## Verification

The dedicated workflow compiles the server and runs the remote service,
Messenger integration, transport, loopback factory, durable anchor, and
activation-gate suites. All storage used by tests is temporary local storage.
