# Mission 23 — Restore Candidate Schema Compatibility

## Objective
Extend restore-candidate validation beyond SQLite page integrity by checking the expected AI Messenger SQLite schema, without changing the candidate or active database.

## Expected schema contract
- `schema_meta` contains exactly the supported version value `1` for key `version`.
- Required tables and columns match the schema produced by `SQLiteMessengerStore`: conversations, messages, idempotency, acknowledgements, and schema_meta.
- The unique conversation/sequence index exists.
- Unknown or future schema versions fail closed.

## Read-only boundary
Validation must open the candidate in SQLite read-only mode. It must not run migrations, create tables, update metadata, or modify rows. It must never receive or open the active database path as a write target.

## Result contract
Return only a boolean and a stable diagnostic code; never return schema contents or file paths. Distinguish unavailable file, SQLite integrity failure, unsupported/missing schema, and successful compatibility validation.

## Explicit exclusions
No schema migration, automatic repair, candidate promotion, live restore, active database replacement, deployment, or physical-device testing. A schema-compatible candidate still requires human review and application-level validation before any separately authorized future promotion.
