# Mission 85 — Read-only identity and conversation membership preflight

## Purpose
Verify that AI-01 and AI-02 are independently provisioned in Firebase and are both members of the configured conversation before any first-contact message is attempted.

## Commands
- `python tools/firebase_first_contact_smoke.py --config-check`: local-only validation; no network access.
- `python tools/firebase_first_contact_smoke.py --preflight`: performs exactly three authenticated RTDB GET operations (AI-A identity, AI-B identity, conversation record). It does not POST, PUT, PATCH, DELETE, send a message, or write an ACK.

## Preconditions checked by --preflight
1. The AI-A identity record exists and its `aiId` matches the configured AI-A ID.
2. The AI-B identity record exists and its `aiId` matches the configured AI-B ID.
3. Both identity records contain nonempty Firebase UIDs and the UIDs are distinct.
4. The conversation record exists and its `members` map explicitly contains both AI IDs with boolean `true` values.

## Successful report
A successful preflight reports:
- `state=PREFLIGHT_PASS`
- both `identity_mappings=VERIFIED`
- both `conversation_membership=VERIFIED_MEMBER`
- `uids_distinct=true`
- `write_operations=NONE`
- `message_round_trip=NOT_RUN`
- `acknowledgement=NOT_RUN`

The output contains no bearer tokens. A failure returns a fail-closed `BLOCKED` result with a reason code, without including request URLs, tokens, or Firebase response bodies.

## Safety
- `--preflight` cannot be combined with `--send` or `--allow-production-send`.
- `--config-check` cannot be combined with network or send options.
- Production send continues to require both the CLI `--allow-production-send` and environment `MESSENGER_FIREBASE_ALLOW_PRODUCTION_SEND=true`, in addition to `--send`.
- This mission does not send production messages, create identities/conversations, publish rules, deploy, or activate physical devices.

## Validation
Tests cover successful three-GET preflight, identity mismatch, duplicate UID, membership denial, no write verbs, CLI option conflicts, output redaction, and the existing Firebase Auth/RTDB Emulator round-trip regression.
