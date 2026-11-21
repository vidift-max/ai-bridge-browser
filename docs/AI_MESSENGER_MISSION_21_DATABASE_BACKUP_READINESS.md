# Mission 21 — Database Backup Readiness

## Objective
Add a conservative SQLite snapshot capability and validate backup integrity without modifying the live database.

## Scope
- Define backup safety and operator-controlled destination rules.
- Implement a SQLite online backup primitive.
- Refuse overwrite and source/destination collisions.
- Verify the resulting snapshot integrity.
- Integrate safe operational diagnostics and add tests/runbook.

## Out of scope
No automated schedule, cloud backup, retention deletion, encryption/key management, restore-over-live, hosted deployment, public endpoint, external provider, or physical Android activation.

## Acceptance
Tests must prove snapshot integrity, source preservation, overwrite refusal, and safe failure codes. Backend and Android workflows must pass on the same final HEAD.
