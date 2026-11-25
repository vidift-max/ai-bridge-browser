# Mission 174 — Trusted Head Witness, Backup and Restore

## Scope and rounds

1. Audit Mission 173 PR #175 and verify both CI runs at its final SHA.
2. Define the local witness journal as a separate artifact with explicit trust limits.
3. Implement strict head validation, append-only history and idempotent exact retries.
4. Reject witness rollback and same-sequence forks.
5. Verify an anchor against the retained witness and detect a rolled-back database.
6. Design backup as a read-only source operation with a precondition witness check.
7. Create backups through SQLite's online backup API and verify SQLite integrity plus chain head.
8. Restore only to a new destination; refuse overwrites and verify before accepting output.
9. Test truncated backup, source rollback, idempotency, immutability and no-overwrite behavior.
10. Run compile and relevant/full CI; inspect exact final-SHA runs/jobs and document limitations.

## Security properties

The witness is append-only within its own SQLite file and stores monotonically
increasing sequence/audit identifiers. Backup is permitted only when the source
matches the witness. Restore refuses an existing destination and accepts a
restored copy only after SQLite integrity_check and full chain verification
against the witness. No operation attempts to repair or overwrite source data.

## Trust and recovery limitations

A separate local file is not automatically an independent trust domain. A
privileged actor able to modify both files can rewrite both. Production use
requires separate administration, access controls, protected off-host storage,
retention, key management and tested disaster-recovery procedures. These tests
use temporary files and do not prove cloud backup, off-site replication,
cryptographic authentication of the witness, or operational RPO/RTO.

No external service, production credential, paid API, deployment or device is
used. No production database is read or changed.
