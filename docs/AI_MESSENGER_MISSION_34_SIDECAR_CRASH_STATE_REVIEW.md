# AI MESSENGER Mission 34 — SQLite Sidecar Absence, Mismatch, and Crash-State Review

**Status: INVESTIGATION COMPLETE; IMPLEMENTATION/CRASH-RECOVERY CERTIFICATION NOT CLAIMED**

## Scope

Review the existing read-only restore-candidate validator and the Mission 33 WAL/SHM/rollback-journal coverage for states in which SQLite sidecars are absent, malformed, stale, or left behind by an interrupted process. This mission is limited to source/test inspection and an operator-facing decision matrix. It does not manipulate live databases, delete sidecars, simulate power loss against real data, change journal modes, or promote candidates.

## Evidence inspected

- `server/backup.py`: `validate_restore_candidate` rejects symlinked path components and non-files, opens the candidate through SQLite URI `mode=ro`, pins one read transaction, and delegates integrity/schema/data checks to the same connection.
- `server/recovery.py`: integrity validation uses `PRAGMA integrity_check`; no sidecar enumeration, repair, deletion, checkpoint, or journal-mode conversion is present.
- `server/test_restore_candidate_data_consistency.py`: current tests cover file-backed DELETE, TRUNCATE, PERSIST, and WAL modes; a concurrent WAL commit; candidate byte preservation; and symlink/hard-link boundary characterization.
- `server/test_backup.py`: online backup API test keeps a WAL writer open and verifies a committed WAL row is present in the backup.
- `docs/AI_MESSENGER_RESTORE_CANDIDATE_OPERATOR_RUNBOOK.md`: operators are told to treat a live database and SQLite-managed sidecars as one storage set and not manually copy/delete sidecars.

## Ten review rounds

### 01/10 — Validator entry boundary
Confirmed that validation starts from the main candidate path and screens the leaf and lexical parent components for symlinks. It does not independently enumerate `-wal`, `-shm`, or `-journal` files.

### 02/10 — Sidecar ownership
Confirmed that sidecar interpretation is delegated to the SQLite library. Application code does not open, rename, unlink, copy, or repair sidecars during candidate validation.

### 03/10 — Absent sidecars
A missing sidecar is not itself treated as an application-level failure. It may be normal for a database using a non-WAL journal mode or after a WAL database has been cleanly closed/checkpointed. The repository does not yet contain a dedicated assertion that a clean standalone candidate with no sidecars validates successfully.

### 04/10 — WAL and SHM distinction
Mission 33 verifies a live WAL fixture with a committed WAL frame and checks that WAL/SHM remain present during validation. It does not establish behavior for every combination of WAL present/SHM absent, SHM present/WAL absent, or both absent while another process remains active.

### 05/10 — Rollback journal states
Mission 33 checks a PERSIST journal sidecar remains unchanged during validation. It does not simulate an interrupted transaction or certify recovery from hot/incomplete rollback journals.

### 06/10 — Malformed sidecar input
No repository test deliberately corrupts a WAL, SHM, or rollback-journal file. The exact result can depend on SQLite's parser/runtime and the fixture's state; do not infer that every malformed sidecar will produce the same diagnostic or be harmless.

### 07/10 — Stale or mismatched sidecars
No test attaches a sidecar left from a different database or proves provenance matching between a main database and companion files. The validator's success must not be interpreted as an external provenance check for the sidecar set.

### 08/10 — Crash interruption
No controlled process-kill, OS-crash, power-loss, torn-write, or filesystem durability test exists in this mission's evidence. Unit tests with open connections are not equivalent to crash-recovery certification.

### 09/10 — Safe test boundary
Future characterization must use disposable temporary directories and isolated SQLite fixtures only. A test may construct deliberately malformed or interrupted sidecar states only if the fixture can be safely discarded; never perform this against the active Messenger database, a user backup, or a production path.

### 10/10 — Operator guidance and release gate
Documented the current guarantees and explicit unknowns below. No implementation change is justified from source inspection alone. Any future behavior change requires a focused fixture, deterministic expected result on the pinned SQLite runtime, byte-preservation assertions where applicable, and both Backend Test and Android Build success on the same final SHA.

## Decision matrix

| Observed state | Current evidence | Safe operator interpretation |
|---|---|---|
| No sidecars beside a closed, standalone candidate | Ordinary candidate success is covered, but absence is not separately asserted | Not inherently an error; SQLite remains the authority when opened |
| WAL and SHM present with an active writer | Covered by Mission 33 fixture for the tested runtime | Do not copy/delete sidecars manually; use SQLite online backup API |
| WAL present, SHM absent | Not specifically covered | Unknown for this repository's supported operating envelope; do not alter files to force validation |
| SHM present, WAL absent | Not specifically covered | Unknown; do not infer corruption or safety from filenames alone |
| PERSIST rollback journal present | Preservation covered by Mission 33 | Do not remove or edit it manually |
| Hot/incomplete rollback journal after interruption | Not covered | Treat as recovery-sensitive; preserve the entire storage set and escalate for controlled SQLite recovery analysis |
| Malformed or truncated WAL/journal | Not covered | Do not assume a stable diagnostic or attempt manual repair |
| Sidecar from another database / stale sidecar | Not covered; provenance not checked | Candidate provenance is unverified; isolate and investigate, do not promote |
| Process/OS/power failure during write | Not covered | No crash-recovery or durability certification is claimed |

## Current guarantees

- Candidate validation uses a single read-only SQLite connection and one pinned read transaction for integrity, schema, and data checks.
- The validator does not itself remove, rename, checkpoint, repair, or promote candidate files.
- Mission 33 tests specific WAL/SHM and PERSIST behavior on the configured local SQLite runtime.
- Backup creation uses SQLite's online backup API; the tested WAL case includes a committed WAL frame while the source writer remains open.

## Explicit non-guarantees

This review does not prove crash recovery, power-loss durability, arbitrary malformed/stale sidecar handling, sidecar provenance, behavior on every SQLite build/filesystem/network share, or safe operation with uncontrolled external writers. CI success is not a physical-device, production, or disaster-recovery test.

## Follow-up recommendation

A later isolated test mission may add narrowly scoped tests for: (1) cleanly closed WAL database with no sidecars, (2) read-only open behavior for WAL/SHM presence combinations using disposable fixtures, and (3) deliberately malformed sidecars with expected outcomes pinned to the CI SQLite version. Crash/power-loss testing should remain a separate, explicitly designed exercise. Until then, preserve sidecars and use the online backup API; do not manually delete, rename, or reconstruct them.

## Final status

**PASS for the 10-round source review and documentation deliverable only.** Runtime sidecar edge cases and crash-recovery readiness remain **NOT PROVEN**. No live database was accessed or changed, no deployment occurred, and no restore/promotion was authorized.
