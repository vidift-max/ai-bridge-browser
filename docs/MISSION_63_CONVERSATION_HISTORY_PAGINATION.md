# Mission 63 — Conversation History Pagination

## Objective
Allow an authenticated conversation member to retrieve older, non-expired messages after they have already been acknowledged, with bounded chronological pages and a browser control that preserves the user's reading position.

## Ten complete work rounds
1. Audited the existing message delivery contract and confirmed that the normal pending endpoint intentionally excludes acknowledged messages.
2. Audited SQLite recovery and retention behavior; message rows remain available until the existing retention policy expires them.
3. Added a room-membership-authorized backend history query with a bounded sequence cursor and page limit.
4. Kept history reads separate from delivery: the history query does not mutate ACK state or the live Long Poll cursor.
5. Added an authenticated HTTP history endpoint with strict query validation, rate limiting, audit event and response metadata.
6. Added backend tests for chronological pages, sender visibility, acknowledged-message retrieval, room isolation and invalid cursor/limit handling.
7. Added HTTP tests for authenticated history retrieval, ACK independence and invalid query handling.
8. Extended the browser messenger adapter with a validated history loader that deduplicates displayed messages and never sends ACK requests.
9. Added the “Carregar histórico anterior” control, chronological prepend behavior, scroll-position preservation, room-switch reset and browser regression coverage.
10. Added this mission record and dedicated Browser/Backend CI workflow; Android sources are untouched by this web/backend mission.

## API contract
- `GET /v1/conversations/{conversationId}/history?before={sequence}&limit={1..100}`
- `before=0` returns the newest page; a positive cursor returns messages with sequence lower than that cursor.
- Responses are chronological (oldest to newest) within each page.
- Only authenticated current conversation members can read history.
- History includes messages sent by or delivered within the conversation, regardless of ACK state.
- Expired messages remain excluded by the existing retention policy.
- The endpoint does not acknowledge messages, advance Long Poll cursors or alter membership.

## Browser behavior
- The user explicitly requests each history page; the normal pending-message/Long Poll path remains unchanged.
- Older messages are prepended in chronological order without jumping the reader to the bottom.
- Already-rendered message IDs are deduplicated.
- The history cursor resets when a different conversation is opened.
- Search and TXT/JSON export continue to operate on messages currently rendered in the active conversation.

## Boundaries
- No WebSocket/SSE transport was enabled.
- No message retention policy was extended.
- No merge, deployment, credential changes or physical-device claims.
- PR remains Draft pending CI and review.
