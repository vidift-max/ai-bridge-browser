# Mission 34 — Guest Room Transport Negotiation

## 10 rounds
1. Revalidated Mission 33 CI as PASS before starting Mission 34.
2. Audited the guest room's current long-poll transport and its future realtime migration boundary.
3. Added an authenticated, room-scoped transport-capability contract.
4. The contract explicitly declares HTTP long polling as the current transport.
5. It publishes the 25-second server maximum and 20-second client default.
6. It explicitly declares WebSocket and generic server push as disabled instead of implying support.
7. It preserves sequence cursors and acknowledgement requirements as part of the transport contract.
8. The guest browser now negotiates the contract before entering the room.
9. Added backend and browser regression tests for authorization and conservative capability reporting.
10. Added dedicated CI and documentation.

## Proof boundaries
- This is capability negotiation, not WebSocket implementation.
- WebSocket and server-push capabilities are explicitly disabled.
- No external AI/provider verification or automation is claimed.
- No deployment or physical-device validation is claimed.
- No transport capability grants additional room permissions; the endpoint is authenticated and room-scoped.
- Long-poll message delivery remains the only implemented realtime-style transport.

## Acceptance
PASS requires the dedicated Mission 34 CI workflow to complete successfully on the final SHA.
