# Restore Candidate Operator Runbook

## Purpose
Create an isolated, integrity-checked SQLite candidate from a known backup for inspection. This is preparation only, not a live restore.

## Preconditions
1. Identify the intended backup through the operator's trusted inventory.
2. Confirm the active database path and choose a different, new candidate path.
3. Ensure the operator has filesystem access and sufficient free space.
4. Preserve the original backup; do not use it as the candidate destination.

## Operation
Call `create_restore_candidate(backup_path, candidate_path)` or the equivalent `OperationalRuntime.create_restore_candidate(..., correlation_id=...)` entry point. The destination must not already exist. The operation verifies the backup, copies it using SQLite's online backup API, and verifies the candidate.

## Expected outcomes
- `RESTORE_CANDIDATE_CREATED`: candidate created and SQLite integrity check passed.
- `RESTORE_BACKUP_UNAVAILABLE`: source file missing or unavailable.
- `RESTORE_BACKUP_INVALID`: source failed integrity validation.
- `RESTORE_CANDIDATE_CONFLICT`: source and destination resolve to the same path.
- `RESTORE_CANDIDATE_EXISTS`: destination already exists and was not overwritten.
- `RESTORE_CANDIDATE_FAILED`: operation could not complete safely.

## Mandatory approval gate
A successful candidate is not approved for production. An operator must independently review provenance, expected application/schema compatibility, message/application-level correctness, and business authorization. Any later promotion must be a separate, explicitly approved procedure with a tested rollback plan and an offline/quiesced active database.

## Safety notes
- Never point the candidate path at the active database.
- Never delete or replace the original backup as part of validation.
- Do not interpret SQLite integrity success as proof of correct business data or schema compatibility.
- This code does not promote, swap, activate, repair, or restore over a live database.
- Keep candidate files under the organization's access controls and retention policy.
