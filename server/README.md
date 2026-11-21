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
