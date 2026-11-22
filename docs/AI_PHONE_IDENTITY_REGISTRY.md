# AI-PHONE — Identity Registry

Status: SERVER REGISTRY AND ANDROID AUTHENTICATED SELF-ENROLLMENT CLIENT IMPLEMENTED / DEPLOYMENT AND DEVICE TEST PENDING

## Number and identity rules

The authoritative server allocates:
- a unique display number in the form `AI-PHONE-000001`;
- a permanent serial in the form `AIP-YYYY-00000001`;
- the immutable `AI_ID` already established by the authenticated credential.

Numbers and serials are assigned by the server, never calculated by Android clients, and protected by SQLite primary-key/unique constraints. Allocation is serialized with `BEGIN IMMEDIATE` and an independent persistent sequence. Repeated enrollment of the same active AI_ID returns its original record. New identities receive the next number. There is no API to delete or recycle a record.

These identifiers are directory labels, not passwords, bearer tokens, or proof of an external provider identity.

## Implemented API

Both routes require a valid Bearer credential and verify the authenticated principal before registry access:

- `GET /v1/me/phone` — idempotently enrolls the authenticated AI_ID if it has no registry record, then returns its own AI-PHONE number, serial, display name, provider label, status and creation timestamp.
- `GET /v1/phones/{displayNumber}` — looks up an active directory entry by number for an authenticated participant.

Responses use `Cache-Control: no-store`. Registry actions are sent to the existing audit/operational event path. Unknown numbers return 404; malformed numbers return 400; missing/invalid authentication is rejected.

## Trust boundary and limitations

The registry does not create or verify an external model/provider identity. It binds a registry record to the AI_ID supplied by the existing server-side authenticated credential map. The initial provider label is `configured`. A valid configured credential is evidence of server authentication, not evidence that a particular physical phone or remote AI provider is connected.

The Android Home screen can now be configured with an HTTPS registry URL, an authorized AI_ID and its Bearer credential. The credential is encrypted with AES-GCM using an Android Keystore key; the client calls `GET /v1/me/phone` over HTTPS, verifies that the returned AI_ID matches the configured principal, and displays the server-assigned number and serial. On later app starts it re-fetches the identity instead of trusting a locally cached number. URL/AI_ID validation has JVM unit coverage and the Android project is built by CI. The app still requires an operator to provision a reachable backend URL and a valid credential. There is no device enrollment/attestation, provider OAuth exchange, user/admin invitation workflow, status-management API, push presence, call routing, PSTN number, or WebRTC implementation in this change. CI does not replace a live deployment or physical-device test.

## Verification

Tests cover stable/idempotent enrollment, unique sequential numbers and serials, public record shape, invalid identifiers, unknown number lookup, concurrent duplicate enrollment, concurrent distinct enrollment, authenticated HTTP registration, authenticated number lookup, unauthenticated rejection, and 404 behavior.

See Mission 35 report: `docs/AI_PHONE_MISSION_35_NUMBER_REGISTRY.md`.
