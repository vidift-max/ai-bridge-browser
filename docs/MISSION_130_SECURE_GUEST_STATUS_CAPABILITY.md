# Mission 130 — Secure Guest Application Status Capability

Status: design and security-contract phase; no endpoint or schema change is implemented by this mission.

## Ten rounds

1. Traced the current public submission route, admin-only review route, and provisioning/revocation lifecycle.
2. Confirmed the public application ID is a 128-bit opaque reference, not an authentication factor; it must remain non-secret.
3. Confirmed the current database stores application status and provisioning status but no guest-owned status capability.
4. Rejected unauthenticated lookup by application ID because it enables enumeration and disclosure of another applicant's decision.
5. Selected a separate 256-bit cryptographically random status capability, generated at successful submission and returned once to the applicant.
6. Required server-side SHA-256 digest storage only; plaintext capability must never be persisted, logged, placed in a URL, or included in analytics/audit events.
7. Defined a capability-authenticated POST lookup contract so the secret is carried in a bounded JSON body rather than query strings, browser history, or referrer headers.
8. Limited the public response to the application's coarse lifecycle state and a server timestamp; exclude display name, provider claim, room/conversation ID, administrator identity, AI identity, membership details, and all credentials.
9. Defined expiry, rate limiting, generic invalid/expired responses, constant-shape errors, and no-access invariants; status capability never authorizes messaging, room entry, provisioning, or credential recovery.
10. Added a CI-enforced design contract and documented the implementation sequence and acceptance tests for the follow-up implementation mission.

## Proposed contract (not yet implemented)

- Submission response: retain the existing `applicationId` and receipt fields; add `statusCapability` exactly once.
- Capability: 32 random bytes (256 bits), URL-safe encoding; persist only SHA-256 digest, bound to one application.
- Lifetime: 7 days from submission; expiry is enforced server-side. Expired capabilities are unusable and should be purged/rotated under retention policy.
- Lookup: `POST /v1/guest-applications/status` with JSON `{"statusCapability":"..."}`; never accept `applicationId` as authorization.
- Public states: `PENDING`, `APPROVED_AWAITING_PROVISIONING`, `REJECTED`, `ACTIVE`, `REVOKED`. Do not expose internal review notes or provisioned identity details.
- Response: `{"status":{"state":"...","updatedAt":"..."}}`; no PII, room identifiers, provider claims, bearer credentials, session tokens, or membership data.
- Security: HTTPS only in deployed environments; bounded body; per-IP and per-capability rate limits; generic 404-style failure for unknown/expired/revoked capabilities; redact request bodies from logs.
- Browser: keep capability in tab-scoped session memory only; do not put it in the invite URL, localStorage, cookies without a separate design, or analytics. Clear it when the tab/session ends.
- Capability is read-only and cannot be exchanged for a guest session, room membership, approval, or credential.
- Admin approval remains separate from provisioning. `APPROVED_AWAITING_PROVISIONING` is not access. `ACTIVE` means provisioning committed, not provider identity verified. `REVOKED` indicates subsequent revocation.
- Idempotent submissions must return the same status capability only if the server can securely recover it; because only a digest is stored, the preferred safe behavior is to avoid returning an unrecoverable secret on a duplicate and instead return a generic duplicate receipt/recovery instruction. The follow-up implementation must resolve this explicitly before coding.

## Required implementation sequence

1. Add a schema migration for `status_capability_hash` and `status_capability_expires_at`; never store plaintext.
2. Generate the capability only after invite validity and idempotency checks are transactionally established.
3. Decide duplicate-submission semantics before returning a token; do not silently mint multiple capabilities or weaken digest-only storage.
4. Add the POST lookup endpoint with strict body validation and rate limiting.
5. Derive status from authoritative application/provisioning rows on every lookup; do not trust cached browser state.
6. Add HTTP tests for pending, approved, rejected, provisioned, revoked, expiry, invalid capability, enumeration resistance, and cross-application isolation.
7. Add tests proving the capability cannot authenticate, provision, join a room, or read admin-only fields.
8. Add redaction tests for logs/audit events and restart persistence tests for digest/expiry.
9. Update the invite page with manual/interval polling only after endpoint implementation and user-facing rate limits are verified.
10. Run full backend, browser, Android, and activation-boundary CI before claiming PASS.

## Explicit non-claims

No status endpoint, schema migration, capability issuance, automatic polling, real guest submission, approval, provisioning, deployment, external AI contact/ACK, or physical-device test was performed in M130. This is a reviewed design contract, not a working feature.
