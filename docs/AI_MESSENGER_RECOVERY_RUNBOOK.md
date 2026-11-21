# AI Messenger — Recovery Runbook

## Startup

1. Validate required runtime configuration.
2. Resolve the configured SQLite path.
3. Verify the database is a regular file when it already exists.
4. Run SQLite integrity check.
5. If integrity succeeds, continue startup.
6. If integrity fails, fail closed with STORAGE_INTEGRITY.
7. Never print database contents or credentials in diagnostics.

## Restart expectation

Messages and idempotency records are expected to survive a normal process restart when the configured SQLite file remains available and intact.

This is a contract/test expectation for the experimental backend. It is not proof of hosted persistent-disk behavior.

## Recovery boundary

A corrupted or unavailable database must not be silently replaced with an empty database, because that could destroy the evidence needed for recovery.
