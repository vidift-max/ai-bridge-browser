# Mission 180 — Native Collective Room Entry

## Objective
Remove the placeholder-hosting URL prompt from the normal `SALA COLETIVA` action in AI Bridge Browser and route the action to the native AI Messenger room already packaged in AI-PHONE.

## Change
- `MainActivity.openCollectiveRoom()` now opens `CollectiveRoomActivityV2` directly.
- The control-center overlay is hidden before navigation.
- The old hosted Rooms URL prompt remains available only through a long-press on the toolbar button, as an optional browser route.
- No Firebase project, URL, API key, identity, room, or invitation is fabricated.

## Evidence
- Commit: `55e4f232f4fad88d4fe642dd8b25b73edea13ed9`
- Branch: `fix/mission-180-native-room-entry`
- Android manifest already registers `CollectiveRoomActivityV2` as a non-exported activity.
- Existing native room UI includes remote Messenger configuration, remote conversation linking, synchronization, and group-invite creation.

## Validation boundary
- Source-level change committed.
- Automated Android build/test result: NOT YET AVAILABLE (the commit has no workflow runs or status checks at the time of this report).
- Installed APK behavior: NOT TESTED.
- Firebase Hosting/Realtime Database deployment: NOT CONFIGURED.
- AI-01 ↔ AI-02 message round trip: NOT PROVEN.
- ChatGPT WebView sessions are not automatically bridged by this navigation change.

## Next required work
1. Run Android build and unit tests for this branch.
2. Complete owner-controlled Firebase project setup and publish the reviewed rules/Hosting.
3. Provision distinct AI-01 and AI-02 identities and a private conversation.
4. Verify one message in each direction and an acknowledgement from the receiving identity.
5. Only then generate and share the working invitation link.
