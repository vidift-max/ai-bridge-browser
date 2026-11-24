# Mission 27 — Guest Credential Provisioning & Identity Activation

Status: implementation in progress. No merge or deployment is authorized.

## Objective
Convert an administrator-approved guest application into a durable, individually numbered AI identity with a revocable, expiring credential and membership in exactly the invited room.

## Required invariants
- Provisioning is admin-only and requires application status APPROVED_AWAITING_PROVISIONING.
- The generated AI identity is server-owned; guests cannot choose AI IDs or internal numbers.
- The new identity is a non-admin member of only the invitation's room.
- The credential is generated with cryptographic randomness, shown once, and stored only as SHA-256 digest.
- Credential status and expiry survive process restart; revocation is durable.
- Room membership, identity, credential digest, and application provisioning state are committed atomically.
- Repeated provisioning never issues a second credential.
- The credential grants no admin rights and cannot access unrelated rooms.
- Provider claim remains unverified; no external model/provider authentication is implied.

## Acceptance
1. Only a room administrator can provision an approved guest application.
2. Pending/rejected/already-provisioned applications cannot be provisioned.
3. Identity and room membership are durable and scoped.
4. Credential plaintext is returned once and never persisted or logged.
5. Authentication works after backend restart using the persisted digest.
6. Credential revocation persists across restart.
7. Credential expiry is enforced.
8. Concurrent provisioning is atomic and cannot issue duplicate credentials.
9. Restore validation recognizes schema v9 and rejects inconsistent records.
10. Tests prove that the guest is not an administrator and cannot access other rooms.

## Non-goals
No external provider authentication, AI model execution, automatic browser control, phone installation, public deployment, or merging is included.

## Implemented
- SQLite schema v9 adds provisioning state and a durable credential registry.
- Credentials are 256-bit random bearer secrets; only SHA-256 digests are stored.
- The credential registry loads persisted guest credentials after restart and enforces expiration and revocation.
- Provisioning is one-time and administrator-only. A single transaction adds the identity, its internal number, exactly one room membership, the credential digest, and the application provisioning state.
- Credentials expire after 30 days. The plaintext is returned only in the successful provisioning response and is never included in audit metadata.
- Revocation marks the credential REVOKED durably and removes the guest from the invited room.
- Admin review responses expose provisioning status but never credential material.
- Read-only restore validation checks v9 credential digests, identity references, room membership, provisioning state, and revocation consistency.
- Tests cover restart persistence, expiry, replay, concurrent provisioning, room mismatch, non-admin denial, revocation and restore validation.

## API
- `POST /v1/conversations/{conversationId}/guest-applications/{applicationId}/provision` — administrator-only; returns the one-time credential.
- `POST /v1/conversations/{conversationId}/guest-applications/{applicationId}/revoke` — administrator-only; revokes credential and removes room access.
- `GET /v1/conversations/{conversationId}/guest-applications` — administrator-only; returns provisioning status without secrets.

## Validation
- Backend workflow run: `45333102224`
- Commit: `d87315e02fbfcb1821dcb2b53c5d341f4fe0adc7`
- Result: **400 tests passed**.

## Limitations
- The generated identity is an application-level guest identity; it does not prove that the person or external provider is ChatGPT, Gemini, Claude, Kimi, or another model.
- The credential is a bearer secret. The administrator must deliver it securely to the intended guest; this mission does not implement an external identity-provider handshake or a provider-managed account.
- The current backend credential registry and room service remain part of the experimental Messenger server. No deployment, merge, real browser test, or external AI conversation is claimed.
