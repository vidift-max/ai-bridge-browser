# Mission 62 — Local Conversation Export

## Objective
Let a user download the messages already loaded in the active conversation as a plain-text transcript or structured JSON file.

## Ten work rounds
1. Audited the active conversation renderer and the existing loaded-message collection.
2. Defined a strict local-only export boundary; no server history fetch is implied.
3. Added a pure export builder for TXT and JSON formats.
4. Preserved message order, sender identity, available timestamps, sequence and exact body text.
5. Added safe conversation-based filenames and correct MIME types.
6. Added local Blob URL download handling with URL cleanup.
7. Added separate TXT and JSON export controls to the conversation UI.
8. Bound exports to the active conversation's currently rendered messages only.
9. Added tests for formats, ordering, malformed rows, validation, filenames and download lifecycle.
10. Added backend static-script serving, cross-platform CI and this mission record.

## Boundaries
- Export includes only messages already loaded and rendered for the active conversation.
- Export is performed locally by the browser; message content is not sent to a new endpoint.
- No message, cursor, ACK, membership, authentication or Long Poll behavior is changed.
- Exported files contain conversation content; the user is responsible for storing and sharing them safely.
- Draft only; no merge or deployment.
