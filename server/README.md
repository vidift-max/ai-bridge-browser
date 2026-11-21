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

## Mission 22 — Controlled restore candidate

Mission 22 adds an operator-triggered `create_restore_candidate` operation. It validates a source backup, copies it to a distinct new path with SQLite's online backup API, validates the candidate, and records a redacted operational event. Existing destinations and source/destination collisions are refused. The operation never promotes or writes to the active database.

SQLite integrity verification is not schema compatibility or business-data validation. Any use of a candidate requires separate human review and a separately authorized promotion procedure with a rollback plan. No live restore, deployment, cloud backup, or physical-device verification is included.

Mission 22 final verification marker: isolated restore-candidate creation from a pre-verified SQLite backup, candidate integrity check, no-overwrite destination policy, source preservation, redacted operational event, and explicit human approval boundary. PASS requires Backend Test and Android Build on this exact final HEAD; live database promotion is excluded.

## Mission 23 — Restore candidate schema compatibility

Mission 23 adds read-only validation of the Messenger schema contract (version 1, required tables/columns, and the unique conversation/sequence index). The combined candidate validator checks SQLite integrity and schema compatibility without running migrations or modifying the candidate. The operational runtime records a redacted validation event. Schema compatibility does not establish business-data correctness or authorize promotion.

Mission 23 final verification marker: read-only Messenger schema compatibility validation for isolated restore candidates, combined with SQLite integrity checks and redacted operational audit. PASS requires Backend Test and Android Build on this exact HEAD. No migration, candidate promotion, or active database modification is performed.


## Mission 24 — Restore candidate data consistency

Mission 24 extends candidate validation with read-only relational checks: every message must reference an existing conversation, its sender and recipients must be conversation members, sequence values must be positive, idempotency rows must point to the matching sender/request message, and acknowledgements must reference an existing message and a conversation member. Invalid candidates are rejected with a stable generic diagnostic. No repair, migration, deletion, or promotion occurs.

Mission 24 final verification marker: read-only Messenger data consistency validation, malformed-reference tests, and redacted operational audit. PASS requires Backend Test and Android Build on this exact final HEAD. No live restore, deployment, or physical-device test is implied.
