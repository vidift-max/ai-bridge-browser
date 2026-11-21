# Mission 33 — SQLite WAL, SHM, and Journal Sidecar Safety

## Scope
Investigate how restore-candidate validation and the SQLite online backup API behave with SQLite-managed sidecars. This mission does not delete sidecars, checkpoint databases, or perform live restore/promotion.

## Work performed (10 rounds)
1. Inspected the validator's read-only URI connection and its lack of manual sidecar manipulation.
2. Reviewed existing journal-mode coverage (DELETE, TRUNCATE, PERSIST, WAL).
3. Identified that WAL-mode data can include committed frames not yet checkpointed into the main database file.
4. Added a test that keeps a WAL writer open with a committed frame while candidate validation runs.
5. Verified in that fixture that the WAL and SHM sidecars remain present during validation and the committed row remains readable.
6. Added a real PERSIST-journal fixture and verified validation leaves its existing journal sidecar present and byte-identical.
7. Added an online-backup test with an open WAL writer and verified the backup includes the committed WAL row.
8. Updated the operator runbook with the main-database-plus-sidecars operational boundary.
9. Updated the server README and this mission report with tested behavior and explicit limitations.
10. Triggered and checked Backend and Android workflows against the final branch HEAD.

## Final commit
Pending final CI completion; recorded in the branch after the final report/README marker.

## Findings
- Validation delegates WAL/SHM handling to SQLite and does not manually copy, delete, rename, or checkpoint sidecars.
- The tested runtime successfully reads a committed WAL frame while a writer connection remains open.
- The tested runtime leaves the observed WAL/SHM sidecars present during validation.
- The tested runtime leaves a PERSIST rollback-journal sidecar present and byte-identical.
- SQLite online backup API captured committed WAL content in a separate backup while the source writer remained open.

## Operational guidance
Treat the database and SQLite-managed sidecars as one live storage set while connections are active. Do not manually copy only the main database file from an active WAL database, and do not manually delete -wal, -shm, or -journal files. Use SQLite's online backup API for snapshots.

## Limitations
All results are scoped to the repository's current SQLite runtime and local test fixtures. They do not certify every filesystem, OS, network share, crash state, or uncontrolled concurrent-writer pattern. No sidecar cleanup, checkpoint, repair, live restore, promotion, or deployment was performed.

## Verification
PASS requires Messenger Backend Test and Android Build to complete successfully on the same final HEAD.
