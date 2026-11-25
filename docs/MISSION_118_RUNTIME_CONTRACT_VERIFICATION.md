# Mission 118 — First Contact Deployment Checklist & Runtime Contract Verification

## Ten-round execution record

1. Confirmed M117 PR #117 and both final CI runs (push 45544410705 and pull request 45544417761) completed SUCCESS on HEAD `ef0230dbedae1855aae1540e6a365521cf14969f`.
2. Compared the Render staging Blueprint start command, health check and runtime configuration against `server/http_server.py` and `server/runtime_config.py`.
3. Audited `GET /healthz` and `GET /readyz`; health is process-level, while readiness validates credentials, storage contract, request timeout, retry limit and operational storage integrity.
4. Found a real runtime mismatch: the Free Blueprint selects SQLite `:memory:`, but the readiness storage checker previously treated every storage target as a filesystem path. An in-memory database has no filesystem file, so `/readyz` returned 503 even with a valid staging configuration.
5. Added a read-only live-connection verifier that runs SQLite integrity, Messenger schema and reference-consistency checks against the active in-memory database.
6. Updated `OperationalRuntime.check_storage` to require the live connection for `:memory:`; missing connection fails closed with `STORAGE_CONNECTION_REQUIRED`. Existing file-backed checks remain unchanged.
7. Wired `/readyz` to the live SQLite connection exposed by the store. It does not create a backup, write test rows, or switch storage mode.
8. Audited the first-contact routes: `GET /v1/me/identity`, `GET /v1/conversations/{id}/messages/wait`, `POST /v1/messages`, and `POST /v1/messages/{messageId}/ack`. The server derives sender identity from bearer authentication; ACK uses the authenticated recipient principal.
9. Added four local HTTP tests: ephemeral `/readyz` returns ready against the live memory database; no-connection memory checks fail closed; the actual local runtime completes identity → Long Poll → submit → receive → ACK → pending removal; and Blueprint entrypoint/port/health contract matches the server.
10. Registered the M118 tests, compile checks and branch filters in CI. Documented the deployment checklist and the default conversation behavior. No Render service, deployment, secrets, external network request, real AI message, paid resource, merge or physical activation was performed.

## Runtime route contract

| Purpose | HTTP contract | Expected result |
|---|---|---|
| Process health | `GET /healthz` | HTTP 200, `status=ok` |
| Runtime readiness | `GET /readyz` | HTTP 200, `status=ready`, only when all runtime and storage checks pass |
| Authenticated identity | `GET /v1/me/identity` | HTTP 200, authenticated `identity.aiId` |
| Receive | `GET /v1/conversations/{conversationId}/messages/wait?after=0&limit=10&timeout=25` | HTTP 200; `principalAiId=AI-02`; message carries sender and sequence |
| Send | `POST /v1/messages` | HTTP 200, `state=QUEUED`, sender AI-01 and exact conversation/recipient/message identifiers |
| Acknowledge | `POST /v1/messages/{messageId}/ack` | HTTP 200, `state=ACKNOWLEDGED`, principal AI-02 |
| Verify pending removal | Repeat Long Poll with `after=sequence-1&limit=100&timeout=0` | ACKed message is not pending |

All authenticated routes require their own bearer credential. Do not send a sender identity field to impersonate another AI. The backend derives the sender from the authenticated principal and restricts receive/ACK to authorized conversation membership and recipient identity.

## Conversation ID for the current staging entrypoint

The current `serve()` bootstrap creates one initial conversation named exactly `default`, with the two configured AI identities as members. Therefore the first-contact runner must use:

```text
conversationId = default
```

Do not assume an arbitrary conversation ID exists. If a different room is needed later, it must be created through the authenticated conversation API and independently verified before using it in the operation-bound approval.

## Free staging readiness behavior

- The Blueprint remains Free, Oregon, manual deploy only, without a persistent disk.
- SQLite `:memory:` remains non-durable and data may disappear on process restart or instance replacement.
- `/readyz` now validates the active in-memory SQLite connection directly instead of attempting to open a filesystem path named `:memory:`.
- File-backed storage readiness continues to use the existing read-only filesystem verification path.
- The live memory verification requires an actual connection; it does not silently substitute a new database or report readiness without checking schema and references.
- The Render start command binds to the platform-provided `PORT` and imports `server.http_server.serve`.

## Operator sequence — still not authorized or performed

1. Owner manually creates/deploys the reviewed Blueprint on Free, only after separate explicit authorization.
2. Configure two distinct bearer credentials privately as `MESSENGER_TOKEN_AI_A` and `MESSENGER_TOKEN_AI_B`; never commit or paste values into logs, GitHub, or chat.
3. Confirm AI identities are AI-01 and AI-02.
4. Confirm `/healthz` and `/readyz` return the expected safe states.
5. Run the offline operator readiness and first-contact preflight checks.
6. Use `conversationId=default` unless another room has been explicitly created and verified.
7. Obtain current explicit user authorization before setting the staging/execution gates and exact origin/conversation/operation bindings in the local operator process environment.
8. Execute only the approved one-time operation; verify identity, AI-02 Long Poll, AI-01 QUEUED response, AI-02 ACKNOWLEDGED response and post-ACK pending removal.
9. Stop, redact evidence, revoke credentials and treat all in-memory data as disposable.

The approval bindings belong in the local operator execution environment, not in the Render Blueprint or the staging server environment. A CI PASS, local HTTP test, `/healthz`, `/readyz`, or offline preflight does not authorize deployment or real first contact.

## Evidence boundary

- Local HTTP integration tests use synthetic identities and synthetic credentials on loopback only.
- CI validates code and local tests; it does not prove a deployed Render service or independent AI runtime.
- No Render service/deploy, credential provisioning, external network contact, real message/ACK, paid resource, merge or physical AI-PHONE activation is claimed.
- HTTP Long Poll remains the sole realtime transport; WebSocket and SSE remain disabled.
