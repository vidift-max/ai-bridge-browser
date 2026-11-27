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

Mission 33 final report: `docs/AI_MESSENGER_MISSION_33_SQLITE_SIDECARS.md`. Final CI gate: Messenger Backend Test and Android Build must both pass on the same final branch HEAD.

## Mission 35 — AI-PHONE number registry

The backend now assigns each authenticated AI_ID a persistent, unique AI-PHONE display number and permanent serial. `GET /v1/me/phone` performs idempotent enrollment for the authenticated principal; `GET /v1/phones/{displayNumber}` provides authenticated directory lookup. SQLite unique constraints and a transaction-serialized sequence prevent duplicate allocation under concurrent registration. Re-enrollment returns the original active record. Registry events are audited.

This is a server-side registry foundation only. It binds the identity already authenticated by the configured credential map; it does not prove an external provider identity or physical device. The Android client is not yet wired to enroll/display the number, and this API is not deployed. See `docs/AI_PHONE_IDENTITY_REGISTRY.md` and `docs/AI_PHONE_MISSION_35_NUMBER_REGISTRY.md`. Mission 35 PASS requires Messenger Backend Test and Android Build success on the same final HEAD; CI does not imply a deployed service or physical-phone communication.

Mission 35 final verification marker: the permanent AI-PHONE number registry and authenticated self/directory endpoints are implemented with atomic SQLite allocation and concurrent-registration tests. Require Messenger Backend Test and Android Build SUCCESS on the exact same final branch HEAD. This marker does not imply Android enrollment integration, deployment, provider identity proof, physical-device connectivity, or voice calling.


## Mission 41 — staging readiness gate

Runtime configuration now rejects duplicate Messenger bearer tokens, duplicate AI_IDs, and malformed AI_ID values. The public `/readyz` endpoint runs the complete two-identity configuration validation and returns 503 rather than reporting ready for an invalid identity map. Regression tests cover both configuration validation and the HTTP readiness response. This is a fail-closed configuration check only: it does not provision credentials, deploy the experimental Render Blueprint, configure persistent hosted storage, or establish real-device communication. Mission 41 PASS for code requires Backend Test and Android Build SUCCESS on the same final HEAD; live staging remains BLOCKED until explicitly approved infrastructure, persistent storage, two distinct secrets/identities, and cross-device verification exist.


## Mission 42 — hosted storage fail-closed contract

Runtime configuration now distinguishes `local`, `persistent`, and `ephemeral` storage modes. The hosted experimental Render Blueprint explicitly declares `ephemeral`, so `/readyz` returns 503 rather than claiming durable Messenger readiness. Persistent mode requires an absolute, existing, writable mount root and a database path strictly below that root. Tests cover invalid modes, ephemeral rejection, root/path containment, and HTTP readiness behavior.

This is an operator-declared path contract, not independent proof of a cloud volume mount or durability. The current Render Blueprint remains intentionally not-ready until an operator provisions and verifies a persistent disk, then supplies the persistent mode/root and two distinct AI credentials through the provider's secret manager. See `docs/AI_MESSENGER_MISSION_42_STAGING_STORAGE_CONTRACT.md`. No hosting resources, secrets, deployment, or external AI connection are created by this mission.


Mission 42 final verification marker: storage mode is explicit and fail-closed; the experimental Render Blueprint declares ephemeral storage and cannot pass `/readyz`; persistent mode validates an operator-declared writable root and database path containment; readiness also checks SQLite integrity through the operational runtime. Regression tests cover configuration, HTTP readiness, and corrupt storage. Require Messenger Backend Test and Android Build SUCCESS on the exact final HEAD. This marker does not prove a cloud disk mount, deployment, real AI credentials, or cross-device communication. Full operator contract: `docs/AI_MESSENGER_MISSION_42_STAGING_STORAGE_CONTRACT.md`; report: `docs/AI_MESSENGER_MISSION_42_PERSISTENT_STORAGE_READINESS.md`.


## Mission 43 — zero-cost local Messenger validation

The current work is intentionally limited to repository code and free local/CI validation. No Render service, disk, database, secret, or deployment is required or authorized. For local development, use the standard-library SQLite backend and distinct test identities/tokens supplied only through the local process environment. Keep the database on a user-controlled local path; back it up before experiments.

Readiness now checks SQLite integrity, the Messenger schema contract, and persisted relationship consistency: every message must have a matching idempotency mapping, and ACK records must belong to actual message recipients. These checks are read-only. A green CI run validates the code and test suite only; it does not create an internet-accessible endpoint or prove communication between separate physical devices.

Free local testing can run two backend/client instances on the same computer or trusted local network. Internet-wide communication, always-on availability, push notifications, and voice calls require separately evaluated infrastructure and must not be described as available merely because local tests pass.


## Authenticated group invitations (experimental API)

The current HTTP server implements these invitation routes:

- `GET /v1/conversations/{conversationId}` — an authenticated current member reads the current server-authoritative membership list; non-members are denied. Clients use this after invitation acceptance to refresh recipients before sending.
- `POST /v1/conversations/{conversationId}/invitations` — an authenticated current group member creates a directed invitation for a target AI_ID that is already provisioned; request fields are `targetAiId` and optional `ttlSeconds` (1–86400).
- `POST /v1/invitations/accept` — the authenticated target AI_ID accepts using the one-time token. The server derives the target identity from the bearer credential; the link alone never grants membership.
- `POST /v1/invitations/{invitationId}/revoke` — only the invitation creator may revoke a pending invitation.

The server generates a URL-safe random token, persists only its SHA-256 digest, binds it to the target identity and conversation, and enforces expiry, single use, and the 20-member GROUP limit in SQLite transactions. PRIVATE conversations cannot be expanded. The Android client currently shares a custom `aibridge://invite/...` link as text; the recipient must paste it into the Messenger invitation screen because no automatic deep-link intent filter is registered.

These routes are experimental code, not a deployed service. The Render blueprint remains not-ready until persistent storage and distinct credentials are provisioned and verified. A successful CI test does not prove a reachable server or cross-device message delivery.

## GPT-6 provider boundary

The current Python HTTP server does **not** expose `/v1/gpt6/status`, `/v1/gpt6/respond`, or `/v1/gpt6/room/respond`. There is no configured GPT-6 provider adapter or provider credential in this backend. Do not call those paths as implemented endpoints or report a native server-backed GPT-6 chat. GPT-6 coordination remains within the existing browser/WebView workflow until a separately authorized, documented backend contract and provider integration exist.
