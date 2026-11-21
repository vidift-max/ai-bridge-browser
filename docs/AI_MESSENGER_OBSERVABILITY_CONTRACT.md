# AI Messenger — Observability Contract

Observability is intentionally local/contractual until a hosted monitoring system is explicitly authorized.

## Required operational fields

- event type;
- UTC timestamp;
- correlation ID when request-scoped;
- authenticated AI principal when available;
- outcome;
- bounded diagnostic code.

## Forbidden fields

- bearer tokens;
- session tokens;
- Authorization header values;
- credentials;
- message bodies;
- private conversation content.

## Event classes

- STARTUP;
- READINESS_OK;
- READINESS_BLOCKED;
- MESSAGE_ACCEPTED;
- MESSAGE_REJECTED;
- MESSAGE_READ;
- MESSAGE_ACKNOWLEDGED;
- STORAGE_RECOVERY;
- STORAGE_INTEGRITY_FAILURE;
- SHUTDOWN.

Events are diagnostic records, not proof of deployment or external connectivity.
