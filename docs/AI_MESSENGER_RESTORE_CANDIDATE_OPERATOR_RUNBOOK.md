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

## Mission 23 — schema compatibility check
After candidate creation, call `validate_restore_candidate(candidate_path)` or `OperationalRuntime.validate_restore_candidate(..., correlation_id=...)`. This performs SQLite integrity validation and then checks the Messenger schema in read-only mode. It expects schema version 1, the required Messenger tables/columns, and the conversation/sequence unique index.

A successful result (`RESTORE_CANDIDATE_VALIDATED`) means only that SQLite integrity and the currently supported schema contract passed. It does not prove business-data correctness, provenance, authorization, or successful application startup. Unsupported or future schemas are rejected without migration or modification.



## Mission 24 — read-only data consistency

After schema compatibility passes, `validate_restore_candidate(candidate_path)` also checks persisted relationships without changing the candidate:
- each message references an existing conversation;
- sender and recipients are members of that conversation;
- sequence values are positive (the schema's unique index enforces per-conversation uniqueness);
- each idempotency row references a message with the same sender and client request ID;
- each acknowledgement references an existing message and a member of its conversation.

A failure returns `RESTORE_CANDIDATE_DATA_INCONSISTENT`. The diagnostic deliberately does not disclose paths, message bodies, or database values. These checks are limited to the fields represented by the current schema; they do not prove delivery history, semantic correctness, identity authenticity, or business authorization. No automatic repair, migration, deletion, or promotion is performed.


## Mission 25 — malformed data and index definitions

Schema validation requires `idx_messages_conversation_sequence` to be a UNIQUE index over exactly `(conversation_id, sequence)` in that order. Merely reusing the index name is insufficient.

The data validator rejects empty conversation membership, malformed comma-delimited ID lists (including empty segments, duplicate IDs, and whitespace-padded IDs), and non-text ID-list storage. It does not trim, repair, or normalize malformed values. Empty recipient lists remain allowed by the current persistence representation. Failures return generic stable diagnostics; raw database values and paths are not included in operational events.


## Mission 26 — snapshot consistency limitation

The current combined validation performs integrity, schema, and relational checks through separate read-only connections. Do not treat the combined result as an atomic snapshot if another process may modify the candidate concurrently. Keep candidate files quiescent during validation. A future implementation must use one read-only connection and one explicit read transaction for all phases, with concurrency and immutability tests. Until then, snapshot consistency is not established.

## Mission 27 — one-transaction validation

The combined `validate_restore_candidate(candidate_path)` now opens a single read-only SQLite connection, begins an explicit read transaction, pins the read snapshot, and executes integrity, schema, and relational-data validation on that connection. The transaction ensures the phases read a consistent database snapshot in the tested SQLite configuration. A WAL-mode regression test commits a concurrent writer change after the integrity phase and verifies that later validation still observes the original snapshot. The candidate is not modified by the validator itself. External writers may still change the file after validation completes; operators should keep candidate artifacts controlled and should not interpret a successful validation as promotion approval or production recovery certification.


## Mission 28 — journal modes and validation resource lifecycle

The combined validator is exercised against file-backed SQLite DELETE, TRUNCATE, PERSIST, and WAL journal modes. These tests establish compatibility only for the repository's current SQLite runtime and test fixtures; they do not certify every SQLite build, filesystem, network share, or concurrent-writer pattern. Validation is read-only and must not change the candidate's journal mode.

The validator now closes its read-only connection deterministically on success and on early diagnostic returns. An unreadable database produces the generic integrity-failure result and also releases the opened connection. Closing the connection ends the read transaction; no candidate repair, journal-mode conversion, checkpoint policy, or promotion is performed.


## Mission 29 — candidate immutability and input boundary

The combined validator accepts only an existing regular file and opens it using SQLite URI read-only mode. Missing paths and directory paths are rejected before opening a SQLite connection. Regression tests verify that a deliberate write attempt through the validation connection is rejected, the candidate's SHA-256 file bytes remain unchanged after successful validation, and paths containing spaces, `#`, and `?` are correctly encoded as file URIs.

These tests establish behavior for the tested local filesystem/runtime only. They do not establish immutability against a separate process with write access, filesystem-level tampering, symlink race resistance, or provenance of the candidate.
