# Mission 35 — AI-PHONE Permanent Number Registry

Status: IMPLEMENTED — FINAL CI GATE PENDING
Repository: `vidift-max/ai-bridge-browser`
Branch: `v2-saas-alpha`

## Goal

Give every authenticated AI participant its own unique, permanent AI-PHONE number and serial, so participants can be addressed by number inside the future AI Messenger. This mission builds the authoritative server registry foundation; it does not claim that calling or live messaging is complete.

## Ten completed rounds

1. **Baseline audit:** verified the existing AI identity model, authenticated-principal boundary, Messenger backend, SQLite store, API routes, and CI workflows. Confirmed the old Android identity object only validated registry-shaped data and did not allocate identities.
2. **Persistent registry:** implemented `server/identity_registry.py` with durable SQLite tables for identity records and allocation sequence.
3. **Atomic number allocation:** used `BEGIN IMMEDIATE` to serialize concurrent allocation and a persistent monotonic sequence.
4. **Uniqueness:** enforced unique AI_ID primary key, display number and serial constraints in SQLite.
5. **Stable enrollment:** repeated enrollment for the same active authenticated AI_ID returns its existing number and serial.
6. **Authenticated self-enrollment:** added `GET /v1/me/phone`, bound to the principal derived from the Bearer credential, not a client-supplied AI_ID.
7. **Directory lookup:** added authenticated `GET /v1/phones/{displayNumber}` with active-record lookup and safe 400/404 behavior.
8. **Audit and response safety:** registry actions use the existing audit/operational event path; JSON responses retain `Cache-Control: no-store`; no credentials are returned.
9. **Regression coverage:** added registry and HTTP tests for stable allocation, uniqueness, invalid identifiers, lookup, concurrent same-identity registration, concurrent different-identity registration, authentication and missing-number behavior.
10. **Documentation and CI:** updated the registry contract and server README; final PASS is conditional on Backend Test and Android Build succeeding on the exact same final branch HEAD.

## API

- `GET /v1/me/phone` — enroll or return the caller's AI-PHONE identity.
- `GET /v1/phones/AI-PHONE-000001` — authenticated directory lookup by assigned number.

Number format: `AI-PHONE-000001`.
Serial format: `AIP-YYYY-00000001`.

The server allocates both identifiers. They are directory identifiers, never authentication secrets.

## Tests added

- `server/test_identity_registry.py`: six tests, including concurrent allocation across independent SQLite connections.
- `server/test_identity_http.py`: four live HTTP handler tests using an ephemeral localhost test server.

## Boundaries — not yet complete

- The registry trusts the AI_ID already authenticated by the current configured credential map. It does not authenticate a third-party model provider or attest a physical phone.
- The Android app is not yet connected to `/v1/me/phone`; no number is yet shown from a live server response on the phone UI.
- No deployment, physical Android device test, push notifications, WebRTC voice, call routing, or PSTN/carrier number is included.
- This is a virtual number inside the AI-PHONE ecosystem and requires the backend to be deployed and reachable before different devices can use the directory.

## Acceptance

PASS only when both Messenger Backend Test and Android Build are SUCCESS on the exact same final SHA. This CI gate verifies repository tests/build only; it does not certify a deployed service or end-to-end communication.
