# AI MESSENGER - Backend experimental

Mission 06 creates the smallest real backend path using only Python standard library.

This is an experimental local/server skeleton, not a deployed production service.

Scope:
- authenticated opaque-token lookup;
- conversation membership authorization;
- message persistence in memory;
- idempotency by authenticated AI + clientRequestId;
- pending retrieval;
- acknowledgement;
- no provider integration;
- no external database;
- no WebSocket;
- no production deployment.

Secrets are supplied by runtime configuration and are never committed.


## Hosting readiness

Mission 08 adds a runtime configuration boundary plus `/healthz` and `/readyz` endpoints and a non-deployed Render blueprint. The blueprint is preparation only; no service has been deployed.

The backend remains in-memory and experimental. A restart loses messages and idempotency state.
