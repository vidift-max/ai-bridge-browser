# Mission 131 — Duplicate Submission and Status Capability Contract

Status: resolved design contract; implementation is intentionally deferred to M132.

## Ten rounds

1. Re-read M130's status-capability proposal and traced the actual public submission route.
2. Confirmed the current idempotency boundary is the unique `(invite_id, display_name)` constraint inside `BEGIN IMMEDIATE`.
3. Confirmed duplicate submissions currently return the existing application row, but there is no applicant secret and no public status lookup.
4. Rejected returning a newly generated server capability on a duplicate: it would either replace the original secret or create multiple independently valid secrets for one application.
5. Rejected storing plaintext capability, reversible encryption without an established key-management contract, and using the non-secret applicationId as authorization.
6. Selected a client-generated 256-bit capability using Web Crypto `crypto.getRandomValues` before the first POST; the same in-memory value is reused only for retries within that live tab.
7. Defined server storage as SHA-256(capability) plus an absolute expiry, committed atomically with the new application row; plaintext is never sent back by the server or persisted.
8. Defined duplicate semantics: same application + matching unexpired capability digest is an idempotent replay; same application + different/missing capability returns a generic duplicate receipt without capability or status disclosure.
9. Defined lost-capability behavior: no recovery or rotation through the public endpoint; the applicant must contact the room administrator using the non-secret receipt code. Legacy applications have no capability and remain admin-visible only.
10. Added CI-enforced contract tests and the M132 implementation sequence; no endpoint or schema change is claimed in this mission.

## Resolved protocol

### Submission request

`POST /v1/guest-applications` accepts exactly:
- `inviteToken`
- `displayName`
- `providerClaim`
- `statusCapability`

`statusCapability` is exactly 32 cryptographically random bytes encoded as unpadded base64url (43 characters). The browser creates it with Web Crypto before the first request and keeps it only in a JavaScript variable scoped to the live invite page. A retry in that same live page reuses the exact same value. It is not placed in the URL, fragment, DOM, localStorage, sessionStorage, cookie, analytics, or logs.

### Atomic persistence and replay

- Schema v10 adds nullable `status_capability_hash` and `status_capability_expires_at` to `guest_applications`.
- New application row, SHA-256 digest, expiry (7 days), and invite-use increment are one SQLite transaction.
- The digest is exactly SHA-256 of the decoded 32 capability bytes, stored as lowercase hex; never store the plaintext.
- Existing unique key `(invite_id, display_name)` remains the idempotency boundary.
- On duplicate, compare the supplied capability digest to the stored digest using constant-time comparison. If it matches and is unexpired, return the same application receipt and mark the result as an idempotent replay; do not increment invite uses.
- If it does not match, return only a generic duplicate receipt (no status capability, no application status, no PII, no status lookup). The caller cannot claim or take over the existing application.
- Legacy rows with NULL capability digest are never upgraded by public duplicate submission.

### Status lookup

- `POST /v1/guest-applications/status` body: `{"statusCapability":"<43-char-base64url>"}`.
- Resolve only by SHA-256 digest; do not accept applicationId as authorization.
- Require unexpired capability. Unknown, expired, and malformed values share a generic not-found response.
- Response is limited to `{"status":{"state":"...","updatedAt":"..."}}`; states are `PENDING`, `APPROVED_AWAITING_PROVISIONING`, `REJECTED`, `ACTIVE`, `REVOKED`.
- State derives from authoritative application and provisioning columns on every request. No room ID, display name, provider claim, admin identity, AI identity, credential, membership or review note.
- Rate limit by source IP and a non-reversible capability fingerprint; never log request bodies or capability material.
- Capability is read-only. It cannot approve, provision, authenticate, join a room, send messages, or recover a guest credential.

### Browser behavior

- Generate one capability per invite-page submission attempt with `crypto.getRandomValues(new Uint8Array(32))`.
- Keep it in a closure variable; retry network failures with the same value. Do not create a new capability for an in-tab retry.
- A reload/new tab generates a different value. If the application already exists, the server returns a generic duplicate receipt and does not reveal its state. The applicant must contact the room administrator; there is no public recovery endpoint.
- Add status polling only after the endpoint is implemented and bounded polling intervals are tested.

## M132 implementation acceptance

1. Migration v10 is backward-compatible and keeps legacy capability columns NULL.
2. New submissions persist only digest and expiry in the same transaction as the application.
3. Same-capability retry is idempotent and consumes one invite use total.
4. Different-capability duplicate cannot retrieve status, PII, or the original capability.
5. Invalid capability encodings and lengths fail closed.
6. Status lookup returns each supported lifecycle state and no extra fields.
7. Expiry, malformed, unknown and cross-application isolation tests pass.
8. Capability never appears in logs, URLs, audit events, HTML, or storage beyond the digest.
9. Capability cannot be used for any room, credential, approval, or provisioning action.
10. Full backend, browser, Android and activation-boundary CI passes before feature claims.

## Explicit non-claims

M131 does not implement schema v10, capability generation, status lookup, browser polling, real invite submissions, approvals, provisioning, deployment, external AI contact/ACK, or physical-device testing. This is a resolved contract and test guardrail, not a working status feature.
