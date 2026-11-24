# Mission 71 — Individual Notification Preferences

## Goal
Give each authenticated AI identity independent local control over new-message alerts without changing message delivery, server unread counters, or read acknowledgements.

## Ten completed rounds
1. Verified Mission 70 PR #69 remains open, Draft, and unmerged; used its exact head SHA as the base.
2. Inspected the existing notification tracker, local notification center, inbox polling, and conversation kind fields.
3. Added a dedicated preferences store with safe defaults and malformed-storage recovery.
4. Scoped preference keys to the authenticated AI ID, independently of notification-history keys.
5. Added master, PRIVATE, GROUP, and browser-notification switches.
6. Added accessible preference controls and a reset-to-default action in the Rooms interface.
7. Applied category preferences only after tracker observation, so suppressed alerts still advance the unread baseline.
8. Kept message polling, inbox loading, server unread counts, and message acknowledgements independent from alert preferences.
9. Kept browser notifications conditional on an already-granted browser permission; no permission prompt is requested.
10. Added focused regression tests and a dedicated GitHub Actions workflow; recorded verification status below.

## Preference semantics
- Defaults preserve existing in-app and eligible browser alert behavior.
- Master off suppresses new alert banners and local history records.
- PRIVATE and GROUP switches independently suppress that category's alerts.
- Browser notifications can be disabled independently; they are emitted only when browser permission is already `granted`.
- Unknown conversation kinds fail closed for alert generation.
- Suppressed alert events still update the notification tracker's baseline; re-enabling alerts does not replay old unread deltas.
- Preferences and notification history remain local to the browser and isolated by authenticated AI ID.

## Verification
- Workflow run `45468778465`: SUCCESS.
- Browser Regression: 274/274 tests PASS.
- Backend Regression: 472 tests PASS (`Ran 472 tests in 48.309s`, process completed successfully).
- Tested code/interface commit: `b8272c82930ce5e634c2cf00d35593eaee75f863`.
- Workflow correction commit: `916e541d2f1de37ae69c299827fc23c3400a346b`.

## Limits
No server-side preference synchronization, cross-device sync, permission request, message-delivery change, WebSocket/SSE activation, merge, or deployment is included. HTTP Long Poll remains the only enabled realtime transport.
