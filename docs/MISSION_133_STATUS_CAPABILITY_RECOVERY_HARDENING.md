# Mission 133 — Status Capability Recovery Hardening

Status: implementation complete; CI validation pending.

## Ten rounds
1. Audited the M132 capability lifecycle from guest submission through status lookup and revocation.
2. Identified that public `updatedAt` did not advance on revocation because no revocation timestamp was persisted.
3. Added nullable `status_capability_revoked_at` to SQLite schema v11; existing rows migrate without fabricated timestamps.
4. Updated the read-only recovery verifier to recognize schema v11 and require the new column.
5. Persisted the authoritative revocation timestamp in the same transaction that removes room membership and revokes the active credential.
6. Included revocation time in the public status timestamp calculation while retaining the minimal state + updatedAt response.
7. Reordered duplicate submission handling so an existing application can be replayed only with its same unexpired capability even after the original invite is expired or revoked.
8. Kept new submissions blocked after invite expiry/revocation; duplicate/mismatched capability responses remain opaque and do not reveal application state.
9. Added regression coverage for revocation timestamp monotonicity, capability retry after invite revocation, denial of new submissions, and v10-to-v11 migration.
10. Added the M133 branch to the existing invite activation CI workflow; no deployment or external invite was performed.

## Safety boundaries
No merge, deploy, secret configuration, real invite, external AI contact/ACK, physical-device activation, or paid resource creation. CI is repository-level evidence only.
