# Mission 162 — Provider Audit Remote Anchor & Monotonic Recovery

## Ten engineering rounds

1. Audited M161 PR #162 and exact-head CI; confirmed it remains Draft/open/unmerged and run 45683049467 passed 46 tests on the exact HEAD.
2. Created isolated branch from M161 HEAD `aab9e08c2137e742e616dc5aab8cbcdd6ad8180c`.
3. Inspected signed checkpoint format and found the remote contract needs the verified checkpoint signature; exposed that signature only after successful local HMAC validation.
4. Defined a transport-neutral remote anchor contract with atomic `read_latest` and compare-and-append operations.
5. Implemented monotonic sequence numbers and previous-record SHA-256 digest chaining.
6. Implemented idempotent publication of the exact already-anchored checkpoint and conflict rejection for same-sequence forks.
7. Implemented remote verification that rejects local checkpoint rollback and checkpoints not yet anchored remotely.
8. Added tests for initial publication, idempotency, monotonic advance, rollback, unanchored local state, tampering, remote outage, and concurrent publishers.
9. Added a JSON Schema contract and Python 3.12 CI with M161 and earlier regression suites.
10. Added this report and opened a Draft PR; no merge or deployment.

## Remote client contract

A production adapter must implement:

- `read_latest() -> null | anchor_record`
- `append_checkpoint(expected_sequence, record) -> stored_anchor_record`

The append operation MUST be atomic compare-and-append. It must reject a stale expected sequence, sequence gaps, a broken previous-digest link, duplicate/forked records, and non-monotonic checkpoint audit IDs. The application verifies the returned record against the exact submitted record and validates its digest.

The record includes a monotonic sequence, prior record digest, checkpoint audit ID/hash/time, original checkpoint HMAC signature, and its own SHA-256 digest. The remote service is responsible for retaining append-only history and authenticating the application. This mission does not prescribe a vendor or credential mechanism.

## Failure and recovery behavior

Remote unavailability raises an error during publication and does not mutate the local audit chain or checkpoint. Verification fails closed when the remote anchor is empty, malformed, ahead of the local checkpoint, or detects a rollback/fork. Re-publishing the exact latest checkpoint is idempotent; publishing a later checkpoint advances the sequence.

## Evidence and security boundaries

Tests use a thread-safe in-memory fake implementing the remote contract. This verifies application-side sequencing, digest chaining, idempotency, conflict handling, and failure behavior. It does NOT prove an actual remote service, durable append-only storage, cross-region behavior, production authentication, network retry semantics, or external backup independence. No remote provider was contacted and no secret was created.

The remote anchor must be deployed in a separate trust domain with durable append-only/monotonic storage. If the remote operator can rewrite or roll back its entire history, this contract alone cannot prevent that. Production adapters and operational monitoring remain future work.
