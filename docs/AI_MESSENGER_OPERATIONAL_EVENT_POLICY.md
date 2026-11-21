# Operational Event Policy

Operational events may contain event type, UTC timestamp, correlation ID, authenticated AI principal, outcome, stable diagnostic code, and bounded non-sensitive metadata.

Never record bearer tokens, authorization headers, credential/session values, passwords, message bodies, or raw request payloads. Metadata keys are filtered by the observability primitive and values are truncated. Event retention is bounded and in-memory only.

Readiness checks verify required runtime configuration and the configured SQLite file integrity. Liveness (/healthz) remains distinct from readiness (/readyz). A readiness failure must return a generic safe diagnostic, not filesystem or database contents.
