# AI-PHONE — Identity Registry Contract

Status: CLIENT MODEL IMPLEMENTED / SERVER REGISTRY NOT IMPLEMENTED
Mission 02 — Round 09/10

## Identifier format

Each registered device receives:
- display number: `AI-PHONE-001`, `AI-PHONE-002`, and so on;
- permanent serial: `AIP-YYYY-000001`, globally unique and never reused;
- immutable participant `AI_ID`, independent of display name, tab index or device label.

These identifiers are administrative references, not passwords, tokens or proof of identity.

## Allocation authority

Only the future authoritative server registry may allocate numbers and serials. Allocation must be atomic under concurrent registration, enforce uniqueness with database constraints, and retain revoked/deleted identifiers as tombstones so they cannot be reassigned. The Android client must never calculate or reserve the next official number or serial.

The registry response must bind the immutable AI_ID, display number, serial, provider and provider subject (where an approved provider adapter supplies one), lifecycle status, and server timestamps. Provider subject binding requires an authenticated provider-authorized exchange; a model name or display name is not proof of a unique participant.

## Lifecycle

`INVITED → ACCEPTED_PENDING_VERIFICATION → ACTIVE`

Alternative states: `DECLINED`, `SUSPENDED`, `REVOKED`. A prepared screen, open app or sent invitation is not evidence of an active or connected participant. Revocation must invalidate sessions and grants on the server.

## Client implementation in this round

- Added immutable `AiPhoneIdentity` model.
- Added explicit `unassigned()` state with null AI_ID, number and serial.
- Added validation for registry-shaped identifiers and lifecycle status.
- Home screen now renders an explicit unassigned/preparing identity state.
- Unit tests cover unassigned identity, a valid registry-shaped record and malformed values.

Important boundary: `fromRegistryRecord` validates format only. It does not authenticate the server, verify a signature, provision an identity, or authorize access. No server registry, database uniqueness constraint, provider adapter, authentication, or device enrollment is implemented.

## Acceptance criteria for future server work

- Atomic allocation and unique constraints for AI_ID, display number and serial.
- Permanent non-reuse of serials, including after revocation.
- Authenticated provider binding and explicit invitation acceptance.
- Server-side status transitions, audit events and session revocation.
- Client accepts registry records only over authenticated, authorized transport.
- Negative tests for duplicate allocation, concurrent allocation, forged client identifiers and revoked sessions.
