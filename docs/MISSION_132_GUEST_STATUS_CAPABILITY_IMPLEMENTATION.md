# Mission 132 — Guest Status Capability Implementation

Status: implementation and automated validation in progress.

## Ten rounds

1. Added strict canonical base64url decoding for exactly 32-byte status capabilities; malformed, non-canonical, padded, short, and oversized values fail closed.
2. Added SQLite schema v10 with nullable capability digest and expiry columns plus a partial lookup index; legacy rows remain NULL and are not retrofitted.
3. Extended guest submission to accept a capability and derive SHA-256 over the decoded random bytes; plaintext is not persisted or returned.
4. Made application creation, capability digest, seven-day expiry, and invite-use increment one SQLite transaction.
5. Changed duplicate handling so only the same unexpired capability digest gets an idempotent replay; missing or different capability receives an opaque duplicate receipt without application ID or status.
6. Added a capability-only public status lookup; applicationId is never accepted as authorization, and unknown/expired/malformed capabilities share a generic 404.
7. Derived public lifecycle state from authoritative application/provisioning columns: PENDING, APPROVED_AWAITING_PROVISIONING, REJECTED, ACTIVE, REVOKED.
8. Limited public response to state and updatedAt; added per-source-IP and per-capability-fingerprint rate limiting. The route does not audit or log request bodies.
9. Updated the invite page to generate capability using Web Crypto, retain it only in live page memory, reuse the immutable first-submission payload on in-tab retry, and poll for a bounded period. No URL, DOM, cookie, localStorage, or sessionStorage persistence.
10. Added backend HTTP lifecycle tests, browser contract tests, and CI wiring. Deployment, real invite use, and physical-device validation remain outside this mission.

## Implemented contract

### Submission

- Browser generates 32 bytes using `crypto.getRandomValues(new Uint8Array(32))`, encoded as canonical unpadded base64url (43 chars).
- Capability is held only in the live invite page's JavaScript variable. Network retry in that page reuses the same value and the original immutable name/provider payload; the form is locked after the first submission attempt.
- The backend validates the encoding and stores only lowercase-hex SHA-256 digest plus a seven-day expiry.
- Digest, expiry, application row, and invite use are committed atomically.
- Existing integrations that omit the optional capability remain compatible, but those legacy submissions have no public status lookup. The current invite page always supplies it.
- Duplicate with matching, unexpired digest returns the original receipt and does not consume another invite use. Duplicate with missing, different, or expired capability returns only a generic duplicate receipt.

### Status endpoint

`POST /v1/guest-applications/status`

Request body contains exactly `statusCapability`. The server hashes decoded bytes and looks up an unexpired digest. It does not accept applicationId or any other identity field as authorization.

Success response contains exactly:
`{"status":{"state":"PENDING","updatedAt":<unix-seconds>}}`

The state is recalculated from current database state on every request. ACTIVE and REVOKED reflect provisioning state. Response excludes display name, provider claim, application ID, room/conversation ID, admin/AI identities, review notes, credentials, and membership.

Malformed, unknown, expired, and mismatched capabilities return the same generic 404. Per-IP and per-capability-fingerprint rate limits apply. The endpoint is read-only: it cannot approve, provision, authenticate, join a room, or send messages.

### Browser

The invite page removes the invite fragment from browser history as before. It generates the capability only when submitting, keeps it in a page-scoped variable, and polls at most six times at five-second intervals after receipt. A page reload intentionally loses the capability; public recovery/rotation is not provided. A new tab with a different capability receives only the generic duplicate receipt.

## Automated coverage

- Schema v10 and nullable digest columns.
- Digest-only persistence and seven-day expiry.
- Same-capability retry, duplicate mismatch, and invite-use accounting.
- PENDING, APPROVED_AWAITING_PROVISIONING, REJECTED, ACTIVE, and REVOKED transitions.
- Unknown, malformed, expired, and extra-field status requests.
- Legacy application without capability remains unqueryable.
- Browser Web Crypto, in-memory-only storage, endpoint contract, and bounded polling.
- Existing Android regression and activation-boundary CI remain required.

## Explicit non-claims

This mission does not deploy or activate the service, configure secrets, create a paid resource, submit a real external invite, contact an external AI, prove AI-01/AI-02 message delivery or ACK, install/activate a physical phone, merge the PR, or claim a production-ready status service. CI results validate repository code only.
