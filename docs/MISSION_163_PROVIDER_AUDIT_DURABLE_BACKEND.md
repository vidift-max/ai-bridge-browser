# Mission 163 — Provider Audit Durable Append-Only Backend

## Ten engineering rounds

1. Audited M162 PR #163 and exact-head CI run 45684116250; confirmed 56 tests passed on HEAD c2c45988d1f830d50b75e5d90d5f86aff9a0f28b. Confirmed PR #163 and predecessor PR #162 remain Draft/open/unmerged.
2. Created isolated branch from the exact M162 HEAD.
3. Inspected the transport-neutral remote-anchor contract and its compare-and-append requirements.
4. Implemented `SQLiteDurableAuditAnchor` as a separate-file durable reference adapter.
5. Added transactional `BEGIN IMMEDIATE` compare-and-append with expected sequence, monotonic audit ID, and previous digest validation.
6. Added append-only UPDATE/DELETE triggers, WAL mode, busy timeout, and synchronous FULL durability setting.
7. Added full-history verification across sequence numbers, record digests, prior links, and audit IDs.
8. Added restart, duplicate, sequence gap, stale writer, chain mismatch, audit rollback, tampering, trigger, and concurrency tests.
9. Added end-to-end publication and verification through the M162 contract using the durable backend, plus Python 3.12 CI.
10. Added this evidence report and opened a Draft PR; no merge or deployment.

## Adapter contract

`SQLiteDurableAuditAnchor` implements the M162 interface:
- `read_latest() -> null | record`
- `append_checkpoint(expected_sequence, record) -> record`

The append uses an immediate SQLite write transaction, checks the expected sequence and prior digest, enforces strictly increasing checkpoint audit IDs, validates the record digest, and commits exactly one next sequence. A competing writer with an outdated expected sequence is rejected. The adapter persists records in a dedicated SQLite file and can reopen them after process restart.

## Durability and append-only controls

The reference implementation enables WAL, `synchronous=FULL`, and a bounded busy timeout. SQLite triggers reject ordinary UPDATE and DELETE statements. A history verifier scans all records and validates sequence continuity, digest linkage, and increasing audit IDs.

## Security and evidence boundaries

This is a durable local reference adapter, not a production remote service. A separate SQLite file is not automatically a separate physical device, host, account, or trust domain. A privileged administrator who can alter the database file or drop triggers can rewrite history; the verifier detects tested tampering but cannot establish immutability against an administrator controlling the database and its backups.

No network transport, remote authentication, cloud service, independent operator, production credentials, or deployment was added. The tests use temporary local SQLite files and threads. They establish application behavior and local persistence in CI, not remote durability, multi-region consistency, or protection from host-level compromise.


## CI validation notes

The first CI attempt exposed two incorrect assertions in the new tests and a pre-existing race in the inherited audit-chain test: independent test threads were all trying to run schema migrations on a brand-new SQLite file. The assertions were corrected, and the inherited concurrency test now initializes its schema before racing independent append connections. This preserves the intended concurrency test while removing unrelated migration contention. The final exact-head CI run is recorded in the PR description.
