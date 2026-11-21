# Mission 22 — Controlled Backup Validation and Restore Preparation

Status: implementation in progress until the final same-HEAD CI gate.

## Objective
Prepare a validated restore candidate from a previously created SQLite backup without replacing, renaming, deleting, or writing to the active database.

## Non-negotiable safety boundary
- The source backup must exist and pass SQLite integrity verification before copying.
- The candidate is written to a separate operator-selected path.
- Existing candidate paths are refused; no overwrite mode exists.
- Source and candidate resolving to the same path is refused.
- The active database path is never opened as a write target by this operation.
- Candidate integrity is checked after the online SQLite backup copy.
- This operation does not activate, promote, swap, or restore over a live database.
- Human review and a separate future change with explicit authorization are required before any candidate could become active.

## Contract
The operation returns a boolean and a stable, non-sensitive diagnostic code. It does not return database contents, credentials, or filesystem paths. Failures are closed and do not imply that the source backup was repaired.

## Verification plan
Test valid candidate creation, invalid/missing backup, corrupt backup, source/candidate collision, existing candidate preservation, candidate integrity, source preservation, and operational event redaction. Backend and Android CI must pass on the same final branch HEAD for PASS.

## Explicit exclusions
No live restore, database promotion, automatic rollback, scheduler, cloud/offsite backup, encryption/key management, retention deletion, deployment, or physical-device verification.
