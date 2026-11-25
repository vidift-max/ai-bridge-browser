# Mission 130 — Secure Guest Application Status Capability Design

## Objective
Define a privacy-preserving way for a guest to check the lifecycle of an application without treating the public application ID or the invite token as an authentication secret.

## Ten rounds completed
1. Re-read the M129 receipt, public intake handler, backend intake method, and SQLite schema.
2. Confirmed the public receipt returns a 128-bit opaque application reference, but no guest status lookup exists.
3. Confirmed the application reference is exposed to the guest and is therefore unsuitable as a bearer secret.
4. Confirmed invite tokens authorize submission and must not be reused as post-submission status capabilities.
5. Confirmed administrator list/decision/provisioning routes require an authenticated room administrator.
6. Defined a separate high-entropy status capability: generate 32 random bytes, encode URL-safe, return once on successful submission, persist only SHA-256 hash.
7. Defined storage lifecycle: store capability hash and expiry with the application; default expiry 7 days; never store or log plaintext capability; revoke capability after expiry or explicit revocation.
8. Defined public lookup contract: GET /v1/guest-applications/status with X-Guest-Status-Token header; never accept applicationId, inviteToken, or a token in query/path as a substitute.
9. Defined minimal response allowlist: applicationId, status, provisioningStatus, statusCheckedAt; no display name, provider claim, conversation/room ID, admin identity, credential, session, or membership data.
10. Defined abuse and continuation boundaries, wrote executable design-contract tests, and wired them into the existing CI workflow.

## Proposed status capability contract (design; not implemented by this mission)
- Token: 32 cryptographically random bytes, base64url without padding; at least 256 bits of entropy.
- Persistence: SHA-256(token) only, unique indexed column; plaintext appears only in the one-time 202 response and guest browser memory.
- Expiration: fixed 7-day expiry from issuance; no silent extension on reads.
- Transport: HTTPS request header `X-Guest-Status-Token`; never URL query, path, referrer, localStorage, analytics, or logs.
- Lookup: hash supplied token and perform constant-time-safe capability validation; return generic 404 for unknown, expired, revoked, or malformed capabilities to avoid enumeration.
- Rate limiting: IP + capability-hash bucket; bounded response size; `Retry-After` on throttling; no aggressive polling (minimum 30 seconds).
- Response allowlist only: `applicationId`, `status`, `provisioningStatus`, `statusCheckedAt`. Do not return PII, room identifiers, provider claims, administrator identity, bearer credentials, session tokens, or membership secrets.
- Lifecycle values: application `PENDING | REJECTED | APPROVED_AWAITING_PROVISIONING`; provisioning `NOT_STARTED | ACTIVE | REVOKED`.
- An `ACTIVE` provisioning status is informational only. It must not return or recreate the one-time guest credential, create a session, or automatically join the guest browser.
- The guest must separately authenticate using the one-time credential delivered through the existing authenticated administrator provisioning flow. A status capability is read-only and never a login credential.
- Application ID alone, invite token, display name, provider claim, and room ID must never authorize status lookup.
- Capability revocation/expiry must not affect the administrator's ability to review or provision the application.
- The public receipt should clearly explain that status checking is optional and that approval/provisioning does not imply an active browser session.

## Security decisions
- A dedicated capability is necessary because application IDs are visible in receipts, support screenshots, and operator workflows.
- Hash-at-rest limits damage from a database read; 256-bit random entropy prevents practical guessing.
- Header transport avoids URL history, proxy access logs, and referrer leakage. Server/proxy logging must redact this header.
- Generic failure responses avoid disclosing whether an application ID exists.
- The status API must not become a guest directory or a route to credentials.

## Not implemented / not claimed
This is an architecture and contract mission only. No migration, endpoint, browser polling, capability issuance, real guest request, approval, provisioning, external AI contact/ACK, deployment, device installation, or merge was performed. M130 tests assert the design boundaries and the existing absence of a public status endpoint; they do not prove runtime capability behavior.
