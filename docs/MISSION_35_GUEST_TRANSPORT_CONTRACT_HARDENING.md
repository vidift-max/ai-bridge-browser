# Mission 35 — Guest Transport Contract Hardening

## 10 rounds
1. Revalidated Mission 34's dedicated CI on its final commit before opening this mission.
2. Added an explicit transport contract version to the authenticated room capability response.
3. Centralized the long-poll limits and exposed the minimum wait, maximum wait, default wait, and maximum batch size.
4. Extended backend regression coverage for the version, room identity, authorization, and published bounds.
5. Added a browser-side transport contract validator with strict schema and version checks.
6. Bound validation to the exact authorized conversation ID before the guest room is opened.
7. Added negative browser tests for wrong room/version, missing authorization, unsupported transport, and invalid bounds.
8. Added regression coverage for cursor/acknowledgement requirements and explicitly disabled WebSocket/server push.
9. Documented the contract compatibility and fail-closed behavior.
10. Added a dedicated CI workflow for browser, backend, and Android regression gates.

## Contract rules
- Only contract version 1 is accepted by this client.
- The response must identify the exact room the guest is entering and set `authorized: true`.
- HTTP long polling is the only accepted default transport.
- Wait bounds must be internally consistent and remain within 0–25 seconds; the default cannot exceed the maximum.
- Batch size must be between 1 and 100.
- Sequence cursor and acknowledgement semantics are mandatory.
- WebSocket and generic server push must be explicitly disabled; unknown or contradictory capability data fails closed.

## Proof boundaries
- This mission hardens capability negotiation; it does not implement WebSocket, SSE, push notifications, or a new transport.
- No automatic fallback to an unimplemented transport is introduced.
- No external AI/provider identity verification or provider automation is claimed.
- No deployment, physical-device test, or real cross-network call is claimed.
- Existing room authorization and long-poll message delivery remain unchanged.

## Acceptance
PASS requires the dedicated Mission 35 workflow to complete successfully on the final commit.
