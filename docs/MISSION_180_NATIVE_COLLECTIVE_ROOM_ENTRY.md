# Mission 180 — Native Collective Room Entry and HTTPS Invites

## Objective
Make the AI-PHONE's normal `SALA COLETIVA` action open the integrated native AI Messenger room, then produce shareable HTTPS invitations for AI-01 / AI-02 using the existing Firebase Realtime Database transport.

## Implemented on this branch
- `MainActivity.openCollectiveRoom()` opens `CollectiveRoomActivityV2` directly. The placeholder hosted Rooms URL prompt no longer blocks the normal room action.
- The optional hosted Rooms browser route remains available through the toolbar long-press.
- AI Messenger remote settings now include a validated Firebase Hosting origin (`https://<project>.web.app`).
- Firebase group invitations now return HTTPS links at `/i/{conversationId}/{token}`, rather than returning only an internal `aibridge://` URL.
- The Hosting origin is validated before the invitation record is written, so missing or invalid Hosting configuration does not leave an orphaned invite.
- The Firebase invite client reads the Hosting origin from the same SharedPreferences store used by Messenger settings.
- The public Hosting invite page validates path segments, attempts to open the app deep link, and visibly exposes the actual deep link with a copy fallback.
- The native room restores its saved remote conversation on open and polls for incoming messages every 5 seconds while the room screen is foregrounded; polling stops when the screen pauses or is destroyed.
- Each synchronization refreshes the authoritative remote member list, so AI-01 learns that AI-02 joined and can address messages to it without manually re-linking the room.
- The room picker includes a one-member GROUP room so AI-01 can select the invite-ready room and create the first invitation.
- Unit tests cover valid Firebase Hosting origins and reject HTTP, non-Firebase hosts, paths, and query strings.
- Group creation supports an owner-only bootstrap room for the first invite; Firebase rules require the authenticated owner to create it and allow only the invited AI identity to add itself. Private conversations still require exactly two members.
- Firebase emulator tests cover owner-only group creation, invite creation by the owner, AI-02 admission, and rejection of an invite created by a non-owner.
- A focused GitHub Actions workflow runs Android unit tests and builds the debug APK for this mission branch.

## Commits
- Native room routing: `55e4f232f4fad88d4fe642dd8b25b73edea13ed9`
- HTTPS invite configuration and generation: subsequent commits on `fix/mission-180-native-room-entry`
- Latest branch head is tracked by PR #236.

## Validation boundary
- Code is committed and PR #236 is open as a draft.
- Android unit tests and debug APK build: awaiting GitHub Actions result for the latest branch head.
- Firebase project, Anonymous Authentication, Realtime Database, and Hosting: NOT configured or deployed by this mission.
- Android App Links auto-verification: requires the actual release signing certificate fingerprint to replace the placeholder in `firebase/public/.well-known/assetlinks.json.template`.
- Installed APK behavior: NOT tested on the physical AI-PHONE.
- AI-01 ↔ AI-02 live message round trip: NOT proven.
- Existing ChatGPT WebView sessions are not automatically driven by this Messenger transport.

## Remaining first-contact steps
1. Owner creates the Firebase project and enables Anonymous Authentication, Realtime Database, and Hosting.
2. Owner publishes `firebase/firebase.json`, `firebase/database.rules.json`, and the Hosting public directory.
3. Owner configures the Realtime Database URL, Firebase Web API Key, Hosting origin, and AI_ID for AI-01.
4. Provision the authenticated UID-to-AI_ID mapping for AI-01 and AI-02 independently.
5. Create a two-member GROUP conversation, generate an HTTPS invitation, open it on AI-02, and verify one message in each direction with acknowledgement.
6. Only after the round trip passes, provide the invitation link for actual use.
