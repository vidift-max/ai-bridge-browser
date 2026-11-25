# Mission 122 — Local HTTP Long Poll Delivery Proof

## Objective

Prove the AI-01 → AI-02 first-contact message lifecycle over the actual HTTP handler,
using only synthetic identities and an ephemeral loopback listener. This mission
does not contact Render or the public internet and does not authorize real contact.

## Ten rounds

1. Re-confirm M121's four CI jobs passed and use its exact HEAD as the base.
2. Trace the existing identity, message submission, Long Poll, ACK, history, and
   persistence routes before adding new tests.
3. Create an isolated M122 branch without changing M121.
4. Add a local HTTP integration fixture bound only to 127.0.0.1 with synthetic
   AI-01, AI-02, and AI-03 credentials and SQLite in a temporary file.
5. Verify the two bearer credentials resolve to distinct authenticated identities.
6. Exercise a recipient Long Poll while AI-01 submits a message, and verify the
   actual HTTP response carries the correct sender, message ID, and body.
7. Verify room membership and recipient-only ACK authorization; sender and
   non-member attempts must be rejected.
8. Verify recipient ACK is idempotent, removes the item from pending delivery,
   and exact submission retry preserves the original sequence while changed
   payload reuse is rejected.
9. Restart the backend against the same temporary SQLite database and verify
   acknowledged history remains available while pending delivery stays empty;
   register the tests in the existing CI workflow.
10. Document the proof boundaries, open a Draft PR, and wait for all CI jobs.

## Test coverage

`server/test_mission_122_long_poll_delivery.py` contains eight local HTTP tests:
identity separation; concurrent Long Poll delivery; sender ACK denial; non-member
poll denial; idempotent recipient ACK and pending removal; exact retry stability;
changed-payload idempotency conflict; and ACK persistence across backend restart.

## Safety and evidence boundaries

- Loopback HTTP only: `127.0.0.1`, ephemeral port.
- Synthetic bearer credentials only; no real secrets are read or emitted.
- Temporary SQLite file only; removed after each test.
- HTTP Long Poll remains the only realtime transport.
- No Render service, deploy, external network, paid resource, real message,
  real ACK, physical phone, authorization gate, or merge is performed.
- A passing CI run proves the local automated contract only; it is not proof of
  an activated AI-PHONE-02 or a real AI-to-AI exchange.
