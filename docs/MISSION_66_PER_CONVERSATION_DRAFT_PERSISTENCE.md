# Mission 66 — Per-conversation composer draft persistence

## Objective
Preserve unsent composer text independently for each conversation so switching rooms or reloading the Rooms page does not discard unfinished work.

## Ten complete work rounds
1. Verified the existing composer is shared across conversations and that switching rooms currently replaces its context.
2. Defined a local-only persistence boundary keyed by conversation ID; no message or draft is sent to the server.
3. Added a dedicated draft-store helper with an injectable Storage-compatible interface.
4. Implemented independent load/save/clear operations and safe handling of malformed stored values.
5. Enforced the existing 5,000-character composer limit and removed storage entries for blank drafts.
6. Added unit tests for isolation, empty drafts, length bounds, malformed data, storage failures and invalid inputs.
7. Served the helper through a no-store, nosniff HTTP route and loaded it on the Rooms page.
8. Wired input and room-switch lifecycle to save the previous draft and restore the selected conversation's draft.
9. Wired successful server-confirmed sends to clear only that conversation's saved draft; failed sends preserve the text and retry behavior.
10. Added static integration assertions, a dedicated Browser/Backend regression workflow and this mission record.

## Behavior and boundaries
- Drafts are stored in the current browser profile's localStorage, one key per conversation.
- Drafts are not transmitted to the backend, included in exports, or shared with other devices/browsers.
- Storage denial/quota failures do not prevent typing or sending; persistence may be unavailable in those cases.
- A draft is cleared only after the existing send operation resolves successfully.
- Existing idempotent retry identifiers, ACK, history pagination and HTTP Long Poll behavior are unchanged.
- WebSocket/SSE remain disabled. No merge or deployment.
