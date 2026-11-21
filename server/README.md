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


Mission 24 final verification marker: restore-candidate integrity, schema, and Messenger relationship validation all use read-only SQLite access. The data checks cover message/conversation membership, idempotency references, acknowledgements, and positive sequence values. PASS requires Backend Test and Android Build on this exact final HEAD; no repair, migration, live restore, deployment, or physical-device test is implied.


## Mission 25 — Restore validation edge-case hardening

Mission 25 strengthens the read-only candidate gates. Schema compatibility now verifies that the required conversation/sequence index is unique and has exactly the expected ordered columns. Data validation parses comma-delimited identifiers strictly: malformed empty segments, duplicate values, whitespace-padded values, and non-text storage are rejected rather than silently normalized or dropped. Empty conversation membership is rejected; an empty recipient list remains representable. Unexpected malformed storage returns a safe generic failure. These checks do not change the candidate.

Mission 25 final verification marker: exact unique-index definition checks, strict identifier-list parsing, malformed-value regression tests, and same-HEAD Backend Test + Android Build. No repair, migration, promotion, deployment, or physical-device verification is implied.


Mission 25 final verification marker: read-only restore validation now verifies the exact UNIQUE conversation/sequence index definition and strictly rejects malformed identifier-list encodings. PASS requires Backend Test and Android Build on this exact final HEAD; no data repair, migration, live restore, deployment, or physical-device test is implied.


## Mission 26 — snapshot consistency investigation

Mission 26 traced the combined restore-candidate validation path and documented a time-of-check/time-of-use gap: integrity, schema, and relational checks currently use separate read-only connections. The combined result is not proven to describe one SQLite snapshot. The safe status is BLOCKED until connection-scoped validators and a single explicit read transaction are implemented and tested. See `docs/AI_MESSENGER_MISSION_26_SNAPSHOT_CONSISTENCY.md`. This investigation does not modify candidates, promote backups, or establish production recovery readiness.

Mission 26 investigation verification marker: Backend Test and Android Build must both pass on the exact final HEAD; CI success verifies repository workflows only, not snapshot consistency.

Mission 26 final HEAD gate: require fresh Backend Test and Android Build success on the same SHA; the documented snapshot-consistency limitation remains BLOCKED until implemented and tested.

## Mission 27 — single-snapshot restore validation

Mission 27 refactors restore-candidate validation to open one SQLite read-only connection, explicitly begin a read transaction, pin the read snapshot, and run integrity, schema, and relational-data checks through connection-scoped validators. Regression coverage asserts a single connection and exercises a concurrent WAL writer commit between validation phases; the validator must return a result from its original snapshot. Public standalone validators remain available. This is local SQLite behavior under the tested WAL scenario, not a production recovery certification or authorization to promote a candidate.

Mission 27 final verification marker: require Backend Test and Android Build success on the exact same final HEAD. No live restore, promotion, deployment, or physical-device verification is included.

Mission 27 final CI gate: combined candidate validation now shares one read-only SQLite connection and explicit pinned read transaction across integrity, schema, and data checks. Regression tests cover single-connection use and a concurrent WAL commit. PASS requires fresh Backend Test and Android Build success on this exact resulting HEAD; CI does not imply live restore, deployment, or physical-device verification.

Mission 27 final verification after diagnostic correction: phase-specific exceptions now retain integrity, schema, and data diagnostic codes while all checks share one read-only pinned transaction. Require Backend Test and Android Build SUCCESS on the exact same final HEAD.


## Mission 28 — journal mode and resource lifecycle verification

Restore-candidate validation is covered for file-backed SQLite DELETE, TRUNCATE, PERSIST, and WAL journal modes. Tests also verify deterministic closure of the read-only connection after success, schema failure, and unreadable-database failure. These are repository CI tests for the configured SQLite runtime, not universal compatibility certification. The validator does not change journal mode, perform a checkpoint, repair the candidate, or promote it.


## Mission 29 — candidate immutability and input-boundary tests

Read-only validation now has regression coverage for unchanged candidate SHA-256 bytes, rejected SQL write attempts on the validation connection, missing and directory inputs rejected before connection, and file paths containing URI-special characters. The checks do not establish protection from external writers, filesystem tampering, symlink races, or backup provenance. No candidate mutation, repair, promotion, or deployment is performed.

## Mission 30 — restore candidate filesystem boundary

The restore-candidate validator rejects a symbolic link in the final candidate path component before opening SQLite. Tests cover valid-target and dangling symlinks and assert that SQLite is not opened. This is a narrow input-boundary check only: parent-directory symlinks, hard links, concurrent path replacement, filesystem tampering, and provenance remain outside the guarantee. Candidate directories must remain operator-controlled. No live restore, promotion, deletion, or deployment is performed.

Mission 30 final verification marker: require Messenger Backend Test and Android Build SUCCESS on the exact same final branch HEAD. CI validates repository workflows only; it does not certify filesystem race resistance or physical-device behavior.

## Mission 31 — symlinked parent path boundary

Restore-candidate validation screens the candidate leaf and lexical parent components for symbolic links before opening SQLite. Regression tests cover both an immediate parent symlink and an intermediate parent symlink, asserting rejection before sqlite3.connect. Existing ordinary-path success coverage remains in place.

The check is not atomic and does not prevent concurrent path replacement, hard-link aliasing, all Windows junction/reparse-point cases, mount-point aliases, or filesystem tampering. Do not treat it as filesystem identity certification. Mission 31 PASS requires Messenger Backend Test and Android Build SUCCESS on the same final HEAD.
Mission 31 detailed report: `docs/AI_MESSENGER_MISSION_31_PARENT_SYMLINK_BOUNDARY.md` records the path-component screening, regression matrix, platform skips, and explicit filesystem-race limitations.

## Mission 32 — hard-link alias characterization

Mission 32 adds a platform-dependent regression test showing that a hard-link alias to a valid restore candidate is currently accepted by the read-only validator and that validation leaves the bytes unchanged through both names. This documents current behavior; it does not reject hard links, prove unique file identity, or establish provenance. See `docs/AI_MESSENGER_MISSION_32_HARDLINK_ALIAS_CHARACTERIZATION.md` and the operator runbook. PASS requires Messenger Backend Test and Android Build on the same final HEAD. No live restore, promotion, deployment, or filesystem race resistance is implied.

## Mission 33 — SQLite sidecar handling

Regression coverage now exercises a committed WAL frame while a writer remains open, verifies validation leaves the observed WAL/SHM sidecars present, checks a real PERSIST journal remains unchanged, and confirms the SQLite online backup API includes committed WAL content. These are tested-runtime observations, not universal filesystem guarantees. Treat the database and SQLite-managed sidecars as one live set; never manually copy only the main database file from an active WAL database or manually delete sidecars. See the operator runbook and `docs/AI_MESSENGER_MISSION_33_SQLITE_SIDECARS.md`. No sidecar cleanup, checkpoint, or live restore is performed by validation.
