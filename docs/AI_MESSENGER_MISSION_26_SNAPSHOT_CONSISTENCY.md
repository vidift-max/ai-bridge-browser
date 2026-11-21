# Mission 26 — Restore Validation Snapshot Consistency

## Status
BLOCKED — investigation completed; implementation intentionally not changed.

## Finding
The current `validate_restore_candidate` sequence calls SQLite integrity, schema, and relational-data validators through separate read-only connections. A file that can be modified concurrently may therefore change between checks. Each individual check is read-only, but the combined result is not proven to describe one immutable database snapshot.

## Evidence reviewed
- `server/backup.py`: `validate_restore_candidate` invokes the three validators sequentially.
- `server/recovery.py`: each public validator opens and closes its own `mode=ro` SQLite connection.
- Existing tests cover malformed schema/data and read-only preservation, but do not exercise concurrent mutation between validation phases.

## Safety decision
Do not claim atomic/snapshot-consistent validation. Do not attempt to lock, copy, modify, or promote an operator's candidate as an unreviewed workaround. No live database or candidate was touched by this investigation.

## Required implementation
1. Introduce connection-scoped internal validators for integrity, schema, and data.
2. Open one SQLite read-only connection for the candidate.
3. Start one explicit read transaction before the first validation read and run all checks through that same connection.
4. Preserve current public diagnostic codes and public helper compatibility.
5. Add tests proving the validators share one connection/transaction, reject concurrent-write attempts where SQLite locking semantics permit, and never modify candidate bytes.
6. Re-run Backend Test and Android Build on the exact same final branch HEAD.

## Limitations
SQLite read transactions provide a consistent read snapshot under the selected journal mode, but this mission has not implemented or tested that guarantee. This report is not a restore approval, deployment, production recovery certification, or physical-device result.
