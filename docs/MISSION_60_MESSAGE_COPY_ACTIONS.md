# Mission 60 — Room Message Copy Actions

## Objective
Give each rendered room message an accessible copy action so users can reuse message text without selecting it manually.

## Ten completed work rounds
1. Audited the existing message renderer and confirmed message bodies are rendered with `textContent`.
2. Defined a client-only copy contract; no server mutation or delivery semantics are needed.
3. Added a small helper that writes the exact message body to an injected clipboard interface.
4. Reject empty/non-string bodies and explicitly report unsupported clipboard capability.
5. Propagate browser permission failures instead of showing false success.
6. Added a per-message copy button with an accessible Portuguese label.
7. Report copy success/failure through the existing live status region.
8. Kept message text rendering safe and unchanged; no HTML interpolation or server-side changes.
9. Added Node regression tests for exact text, invalid input, unavailable clipboard, permission failure, and UI wiring.
10. Added a dedicated Browser/Backend/Android workflow and Draft PR.

## Boundaries
- Copy is a local browser action; it does not send, edit, delete, or acknowledge messages.
- Clipboard access occurs only after the user's click.
- No message text is sent to a new service or external AI.
- Existing authentication, room membership, server persistence, and HTTP Long Poll behavior are unchanged.
- No merge or deployment is performed.
