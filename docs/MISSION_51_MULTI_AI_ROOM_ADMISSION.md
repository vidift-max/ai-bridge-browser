# Mission 51 — Multi-AI room admission

## Objective
Move from individually authenticated provider sessions to a room-level collaboration contract: stable AI identity, coordinator-controlled invitations, one-time admission, participant roles, bounded capacity, and individual revocation.

## Ten rounds
1. Verified Mission 50 exact SHA `1ef74312e0524a74f07287862eba935bc5f23057`; Backend, Browser, and Android CI all succeeded.
2. Audited the existing guest-room and provider-session contracts and confirmed HTTP Long Poll remains the only enabled realtime transport.
3. Defined room membership as a separate authorization boundary; membership never grants provider tools or external account access.
4. Created isolated branch `feat/mission-51-multi-ai-room-admission` from the verified Mission 50 SHA.
5. Implemented room creation bound to one connected coordinator session and stable AI identity.
6. Implemented coordinator-issued, single-use invitations bound to one AI identity, a role, and a maximum ten-minute expiry.
7. Implemented admission checks for connected session binding, duplicate identity/session, and configurable bounded capacity (default six).
8. Implemented PARTICIPANT and read-only OBSERVER roles, room-message authorization, member leave, and individual revocation without affecting other members.
9. Added automated tests for identity mismatch, invitation reuse/expiry, disconnected sessions, capacity, role restrictions, revocation isolation, closure, and snapshot secrecy.
10. Added mission documentation and a dedicated Backend/Browser/Android CI workflow; opened a Draft PR for review without merge or deployment.

## Contract
- Roles: COORDINATOR, PARTICIPANT, OBSERVER.
- The coordinator is established at room creation from an already CONNECTED session.
- Invitations are single-use, identity-bound, role-bound, and expire within ten minutes.
- A participant must present the exact invited AI identity and a currently CONNECTED session.
- Default room capacity is six participants including the coordinator; configurable hard maximum is 32.
- OBSERVER is read-only. PARTICIPANT may pass the room-level send authorization check.
- Room membership does not grant tool permissions, provider API permissions, account login, or arbitrary browser access.
- Revocation blocks only the selected member; other active participants remain authorized.
- Closing a room invalidates pending invitations and marks all members closed.
- Public room snapshots omit invitation records and credentials.

## Limitations
- This is an in-memory host-side contract, not durable server persistence or a live web UI integration.
- The session registry is supplied by the trusted host; this module does not authenticate provider proofs itself.
- It does not connect ChatGPT, Claude, or Gemini accounts, nor prove a physical device is online.
- HTTP Long Poll remains the only enabled transport; WebSocket and SSE remain disabled.
- No paid API, merge, or deployment was activated.

## Validation
`node --test web/ai-room-admission.test.mjs`
