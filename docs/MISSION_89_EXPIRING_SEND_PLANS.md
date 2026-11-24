# Mission 89 — Expiring send plans and envelope integrity

## Objective
Ensure a locally saved dry-run plan is accepted only during a short validity window and that expiry and all decision-bearing metadata are covered by its integrity digest.

## Plan schema v2
- New plans use `schema_version: 2`.
- `created_at_epoch_ms` is copied from the proposed message timestamp.
- `expires_at_epoch_ms` is exactly ten minutes after creation.
- Validation rejects timestamps more than 30 seconds in the future and rejects plans after their expiry (the exact expiry millisecond remains valid).
- The canonical `plan_sha256` covers the plan schema, state, preflight state, sender/recipient/conversation binding, operation, creation/expiry timestamps, payload and safety metadata. The payload also retains its own SHA-256 digest.
- The validator accepts an injected `now_ms` for deterministic boundary tests; normal CLI use reads the system clock.

## Security boundaries
SHA-256 detects accidental or unsophisticated modification; it is not a digital signature, does not authenticate the operator, and does not prevent a party able to rewrite the plan and recompute hashes from forging it. Expiry limits the acceptance window but is not one-time replay protection. The file remains credential-free and local verification makes no Firebase request.

## Safety
No production write operation is added or enabled. Plan creation still performs only the existing authenticated read-only preflight GETs. The actual send path remains separate and requires the existing dual production opt-in.

## Validation
Added tests for the exact expiry boundary, expired plans, future timestamps, altered expiry, protected envelope metadata and boolean timestamp rejection. The full Auth/RTDB Emulator HTTP round-trip and existing Python regression suites remain in the workflow.
