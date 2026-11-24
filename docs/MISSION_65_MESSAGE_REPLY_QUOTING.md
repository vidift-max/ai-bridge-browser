# Mission 65 — Message Reply and Quote Drafts

## Objective
Let a participant start a contextual reply from any loaded message without changing the server message contract or silently sending content.

## Ten complete work rounds
1. Reviewed the current message rendering lifecycle and confirmed messages already expose sender identity and body text to the UI.
2. Chose a client-side draft-only interaction because the backend has no threaded-reply contract; no reply endpoint or metadata is invented.
3. Added a dedicated reply helper with strict message-body validation and a generic sender fallback.
4. Implemented readable quote formatting that prefixes every original line and preserves multiline text.
5. Bounded quoted source text to 4,000 characters so a long source message cannot overwhelm the 5,000-character composer.
6. Added unit tests for multiline formatting, sender attribution, missing/blank content and quote-length bounds.
7. Added an accessible “Responder” action to rendered messages using DOM APIs and text values only.
8. Wired the action to populate and focus the existing composer, place the cursor at the end, and tell the participant to review before sending.
9. Added a no-store JavaScript route in the HTTP server and loaded the helper from the Rooms page.
10. Added static integration assertions, a dedicated Browser/Backend CI workflow and this mission record.

## Behavior and boundaries
- Reply creates an editable local composer draft; it does not send automatically.
- The original message is quoted as plain text with `>` prefixes. No HTML injection is used.
- Long quotes are truncated with an ellipsis at the helper boundary.
- The feature does not add server-side threading, reply IDs, notification semantics, or message-kind changes.
- Existing reliable send/idempotency, ACK, history pagination, inbox summaries and HTTP Long Poll behavior are unchanged.
- WebSocket/SSE remain disabled. No merge or deployment.
