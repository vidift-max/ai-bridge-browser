# Mission 180 — Native Collective Room Entry and HTTPS Invites

## Objective
Make the AI-PHONE's normal `SALA COLETIVA` action open the integrated native AI Messenger room, then produce shareable HTTPS invitations for AI-01 / AI-02 using the existing Firebase Realtime Database transport.

## Ten completed engineering rounds

1. Audited the Mission 180 branch, PR #236, workflow, and exact branch head.
2. Verified the normal `SALA COLETIVA` action opens `CollectiveRoomActivityV2`; the legacy hosted Rooms URL is only an optional long-press route.
3. Verified the Firebase Hosting origin is validated as HTTPS `.web.app` and is read from the same Android preference store used by Messenger settings.
4. Verified invite creation requires an existing GROUP, owner identity, and owner membership; URL validation occurs before invite persistence.
5. Verified the invite page parses safe route segments, attempts the app deep link, and exposes a manual deep-link fallback.
6. Verified group bootstrap permits exactly the owner as the initial member; PRIVATE conversations still require two members.
7. Verified Firebase rules require an authenticated owner to create invites and the invited AI identity to redeem and join; non-owner invite creation is rejected.
8. Verified the room picker can select an owner-only GROUP, restores the saved room, refreshes remote members, and polls every five seconds only while foregrounded.
9. Ran the Firebase Realtime Database emulator tests, Firebase rules parity regressions, Android unit tests, and debug APK build on the exact CI head.
10. Inspected the published APK artifact, computed its SHA-256, and documented the owner-side Firebase/device activation and first-contact acceptance criteria.

## Exact validation evidence

- Repository: `vidift-max/ai-bridge-browser`
- Branch: `fix/mission-180-native-room-entry`
- PR: #236 — Draft, open, not merged
- CI run: `45928506821`
- CI head: `0af47031f6483775465764392d0dfe463da41f35`
- Workflow conclusion: SUCCESS
- Firebase emulator security rules tests: SUCCESS
- Firebase rules parity regressions: SUCCESS
- Android unit tests: SUCCESS
- Debug APK build: SUCCESS
- Artifact: `ai-phone-mission-180-debug-apk`, ID `15167278030`
- APK filename: `app-debug.apk`
- APK size: 55,747,106 bytes
- APK SHA-256: `91f0d6b48f430d4bb6a98d887f9d85281e2e46fc245edac1e3f75ce1e1b59363`

The artifact is a DEBUG APK, not a release-signed installer. Its build is verified; installation and runtime behavior on physical devices are not.

## Implemented on this branch

- `MainActivity.openCollectiveRoom()` opens `CollectiveRoomActivityV2` directly.
- AI Messenger remote settings include a validated Firebase Hosting origin.
- Firebase group invitations return HTTPS links at `/i/{conversationId}/{token}`.
- The Hosting origin is validated before the invitation record is written.
- The public invite page validates path segments, attempts the app deep link, and visibly exposes the deep link with a copy fallback.
- The native room restores its saved remote conversation and polls every five seconds while foregrounded; polling stops when paused or destroyed.
- Each sync refreshes the authoritative remote member list.
- The room picker includes a one-member GROUP room for invite creation.
- Unit tests cover Firebase Hosting origin validation and group member parsing.
- Emulator tests cover owner-only group creation, owner invite creation, AI-02 admission, and non-owner rejection.

## Remaining external activation blockers

These actions require the project owner's Firebase account and the two physical devices; CI cannot safely perform them:

1. Create/choose the real Firebase project; enable Anonymous Authentication, Realtime Database, and Hosting.
2. Deploy `firebase/database.rules.json` and `firebase/public` using `firebase/firebase.json`.
3. Configure the real database URL, Firebase Web API key, Hosting origin, and AI_ID separately on AI-01 and AI-02.
4. Provision the two UID-to-AI_ID identity mappings through a trusted administrative bootstrap. Client rules intentionally deny writes to identity maps.
5. Install the APK on both devices, authenticate independently, and verify both identity mappings.
6. Create the owner-only group on AI-01, generate the actual HTTPS invite, redeem it on AI-02, and verify one acknowledged message in each direction.

Detailed steps and acceptance criteria: [MISSION_180_OPERATOR_ACTIVATION.md](MISSION_180_OPERATOR_ACTIVATION.md).

## Validation boundary

- Code is committed to the branch and PR #236 remains Draft/open.
- CI tests and debug APK build are green on the exact SHA above.
- Firebase project, Authentication, Realtime Database, and Hosting are NOT configured or deployed by this mission.
- Android App Links auto-verification is NOT proven; the asset links template still requires the actual signing-certificate SHA-256 fingerprint.
- APK installation and physical device behavior are NOT tested.
- AI-01 ↔ AI-02 live message round trip is NOT proven.
- Room polling works only while the room screen is foregrounded; no persistent background service is claimed.
- This Messenger transport does not autonomously drive the two ChatGPT WebView sessions.

No merge, deployment, release, secret provisioning, or device installation was performed.
