# Mission 56 — Participant Directory & Presence UI

## Objective
Turn the room's compact participant badges into a readable participant directory with server-derived identity and presence details, filters, and manual refresh.

## Ten work rounds
1. Audited the existing authenticated room-identity endpoint and its membership authorization.
2. Verified that identity numbers/names come from the server-owned directory, not browser-supplied values.
3. Verified that online/offline and active-in-room status are calculated by the server's TTL-based presence service.
4. Replaced compact participant badges with a structured directory panel and accessible live count.
5. Added identity number, display name, AI ID, and explicit online/offline state to each participant card.
6. Added last-activity display with a safe fallback when no heartbeat is recorded.
7. Added filters for all participants, online, offline, and active in the current room.
8. Added manual refresh, busy-state handling, and a stale-response guard when the selected room changes.
9. Added regression coverage for rendering, filters, safe text insertion, endpoint authorization, TTL semantics, and refresh behavior.
10. Added the mission workflow and documentation; opened the follow-up Draft PR without merging or deploying.

## Boundaries
- This is a read-only participant directory; it does not add unsupported member-removal controls.
- Server-side room membership and identity data remain authoritative.
- Presence means a valid heartbeat within the server TTL, not proof that an AI model is actively thinking or responding.
- No external AI provider or physical phone was connected or activated.
- HTTP Long Poll remains the only enabled realtime transport.
