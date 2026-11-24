# Mission 51 — Provider Room Admission

## Goal
Bridge authenticated provider sessions into collective AI rooms through explicit, durable, room-scoped admission. A provider session is not a room member merely because its handshake succeeded.

## Contract
- The server-side session registry authenticates the session and credential generation.
- The AI identity is derived from the authenticated session record; callers cannot supply or spoof it.
- An explicit authorization callback must approve every admission and revocation.
- Room roles are limited to COORDINATOR, PARTICIPANT, and OBSERVER; at most one active coordinator exists per room.
- A session can see a room roster only while it has an active admission to that room.
- Revocation removes the active admission from subsequent room listings.
- Credential rotation/revocation/expiry invalidates old session bindings at the next authenticated operation.
- Multiple provider identities can be admitted to the same room, enabling collective conversations.

## Scope and limitations
This is a backend admission primitive, not a deployed provider connector or live AI conversation. It does not log into provider websites, transfer account cookies, enable arbitrary browsing, or prove GPT-6/Claude connectivity. The existing HTTP Long Poll remains the only enabled realtime transport. Network routes and UI wiring are future work.

## Ten rounds
1. Verified Mission 50 CI PASS on its final SHA.
2. Audited provider session, room membership, and presence boundaries.
3. Identified the missing bridge: authenticated sessions had no durable room admission.
4. Created an isolated Mission 51 branch from the validated Mission 50 SHA.
5. Added a durable room-admission schema and explicit authorization boundary.
6. Bound provider and AI identity to the authenticated session record.
7. Added room roles and single-coordinator enforcement.
8. Added room-scoped roster visibility and explicit revocation.
9. Added regression tests for authorization, identity spoofing, multi-provider admission, expiry, rotation, and revocation.
10. Added mission documentation and CI workflow; opened a Draft PR for review.

## Validation
Backend suite: `python -m unittest discover -s server -p 'test_*.py' -v`.
