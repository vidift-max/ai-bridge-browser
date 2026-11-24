# Mission 30 — Guest Presence Lifecycle

## Objective
Make the browser guest participant's online state explicit and bounded while preserving the existing authenticated room boundary.

## 10 rounds
1. Audited the existing server presence contract and guest session lifecycle.
2. Reused the authenticated presence heartbeat endpoint; no new privilege path.
3. Restricted active presence to the single room already authorized by the guest messenger.
4. Added a 15-second browser heartbeat while the guest room is active.
5. Added visibility-aware heartbeats so background tabs do not claim active room presence.
6. Added explicit presence leave on logout.
7. Added best-effort presence cleanup on page teardown without persisting the session token.
8. Added visible status guidance and safe error handling.
9. Added regression coverage for heartbeat, leave, visibility, and timer lifecycle.
10. Added a dedicated CI workflow and documented limitations.

## Security boundaries
- The browser still sends only its short-lived bearer session.
- The server's existing heartbeat_presence authorization determines which rooms can be marked active.
- A guest cannot claim a room it is not a member of.
- No provider verification or external AI automation is introduced.
- Presence is advisory state, not proof that a human or external AI is actively reading messages.

## Limitations
Presence is not a persistent identity signal and may briefly remain stale after abrupt network/device termination. The existing server expiry policy remains authoritative.
