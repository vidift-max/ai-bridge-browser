# Mission 27 — Single-Snapshot Restore Validation

## Scope
Implement combined restore-candidate validation over one SQLite read-only connection and one explicit read transaction.

## Changes
- Added connection-scoped validators for SQLite integrity, Messenger schema compatibility, and Messenger relational consistency.
- Preserved the public path-based validator functions and their diagnostic result codes.
- Refactored `validate_restore_candidate` to open one `mode=ro` connection, execute `BEGIN`, pin the read snapshot with a schema read, and run all three validation phases through that connection.
- Added a regression test asserting that the combined validator opens exactly one SQLite connection.
- Added a WAL-mode concurrency test: a writer commits an invalid sender after the integrity phase; the ongoing validation must continue to observe its original read snapshot and pass, while a subsequent independent validation detects the changed data.
- Updated operator documentation to explain the guarantee and its limits.

## Safety
No candidate is written, repaired, migrated, deleted, or promoted by validation. No active database restore or deployment was performed.

## Verification
Implementation is complete; final status is pending fresh Backend Test and Android Build workflows on the exact same final HEAD.

## Limits
The test demonstrates snapshot consistency for the exercised SQLite WAL scenario. It does not certify all filesystem/journal modes, application recovery, provenance, identity authenticity, business correctness, production operations, or authorization to promote a candidate.
