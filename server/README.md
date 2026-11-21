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


## Mission 14 verification marker

Authorization/audit hardening was completed in Mission 14. The server test workflow is expected to validate the final branch HEAD; this remains an experimental, non-public backend.


## Mission 16 verification marker

Transport reliability hardening was implemented through Mission 16 Round 10. This marker intentionally touches the server workflow path so the final reliability HEAD receives a fresh Backend Test gate. PASS remains contingent on Backend Test and Android Build succeeding on this exact resulting HEAD.


## Mission 18 final verification marker

Mission 18 completed the staging deployment contract preparation. This server-path marker intentionally triggers the Backend Test workflow so Mission 18 can receive the required same-HEAD Backend Test + Android Build verification. No deployment is implied.


## Mission 19 final verification marker

Mission 19 completed the hosted-staging observability and failure-recovery contract/primitives. This server-path marker intentionally triggers a fresh Backend Test on the final Mission 19 HEAD. PASS requires Backend Test and Android Build to succeed on this exact resulting HEAD. No deployment, public endpoint, production monitoring, or external AI connectivity is implied.


Mission 20 final verification gate: operational runtime integration, bounded secret-safe event buffer, SQLite integrity readiness check, and HTTP audit forwarding. PASS is conditional on backend and Android workflows succeeding on the same HEAD; no deployment or physical-device verification is implied.


Mission 21 final verification gate: manual non-overwriting SQLite online backup, independent integrity verification, source-preservation tests, and safe operational event integration. PASS requires backend and Android workflows on the same final HEAD. No cloud backup, encryption, automated retention, restore-over-live, or deployment is implied.
