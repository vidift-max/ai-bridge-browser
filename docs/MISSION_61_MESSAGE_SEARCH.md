# Mission 61 — Conversation Message Search

## Objective
Allow users to find text and sender identities among messages already loaded in the active conversation.

## Ten work rounds
1. Audited the existing message renderer and confirmed the UI only holds currently loaded messages.
2. Defined an explicitly local search scope; no claim of searching server history beyond loaded messages.
3. Added a pure helper for case-insensitive body and sender matching.
4. Added optional exact sender filtering that composes with text search.
5. Added a search field and live result count in the active conversation.
6. Preserved original message order and existing message action buttons.
7. Reapplied search after incoming messages are appended.
8. Added a clear-search action and empty-result feedback.
9. Added browser tests for matching, filtering, trimming, malformed input, and safe UI wiring.
10. Added backend static-script serving, cross-platform CI, documentation, and Draft PR.

## Boundaries
- Search covers only messages currently loaded in the browser for the active conversation.
- It does not fetch older history, change cursor/ACK behavior, or modify server data.
- Search is local and does not transmit message content.
- Existing authentication, room membership, copy action, and HTTP Long Poll remain unchanged.
- Draft only; no merge or deployment.
