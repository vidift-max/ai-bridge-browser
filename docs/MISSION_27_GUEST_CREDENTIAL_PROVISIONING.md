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
