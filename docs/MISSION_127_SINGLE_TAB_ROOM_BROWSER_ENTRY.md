# Mission 127 — Single-Tab Collective Room Browser Entry

## Objective
Expose the existing web group-room experience from the AI Bridge Browser chrome without opening a separate tab for each AI or launching a separate activity.

## Ten rounds
1. Confirmed M126 final CI: push and pull-request runs completed successfully on the same final SHA; PR #126 remains Draft and unmerged.
2. Audited MainActivity: the browser has six WebView tabs, a separate AI Control Center, and no collective-room shortcut.
3. Audited CollectiveRoomActivityV2 and confirmed it is a separate native activity, not a browser tab.
4. Audited the existing web Rooms page and its shared participant/message adapter.
5. Defined a narrow HTTPS route contract for the hosted Rooms page.
6. Implemented a pure Java validator that accepts only HTTPS `/rooms` or `/rooms.html` routes and rejects credentials, explicit ports, query strings, fragments, and other paths.
7. Added JVM tests for valid and invalid room routes.
8. Added a browser-chrome action that asks for the hosted Rooms URL once and stores it in local browser preferences.
9. Connected the action to the currently selected WebView; it reuses that tab and never calls addTab. Added browser contract tests.
10. Updated CI branch filters/test command and recorded the implementation boundaries.

## Evidence boundaries
- The Rooms page, invite link flow, and room messaging adapter already exist in the web project.
- This mission adds a browser entry point into a user-configured hosted Rooms page; it does not host/deploy that page or configure its real URL.
- The shortcut opens the page in the currently active WebView. It does not create a separate tab per AI.
- No invitation was redeemed, no external AI was contacted, no real message/ACK was sent, no Render/Firebase deployment occurred, and no device installation test was performed.
- The configured URL must be supplied by the operator and point to an actually hosted Rooms page. Until then, the shortcut prompts for configuration.
