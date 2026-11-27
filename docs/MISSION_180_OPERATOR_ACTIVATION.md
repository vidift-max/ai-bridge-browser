# Mission 180 — Operator Activation Checklist

## Current verified build

- Repository: `vidift-max/ai-bridge-browser`
- Branch: `fix/mission-180-native-room-entry`
- PR: #236 (Draft; not merged)
- Verified commit: `0af47031f6483775465764392d0dfe463da41f35`
- GitHub Actions run: `45928506821` — SUCCESS
- Artifact: `ai-phone-mission-180-debug-apk` (artifact ID `15167278030`)
- APK: `app-debug.apk`, 55,747,106 bytes
- APK SHA-256: `91f0d6b48f430d4bb6a98d887f9d85281e2e46fc245edac1e3f75ce1e1b59363`

This is a DEBUG APK. It is not a Play Store/release-signed build. Its build success does not prove installation, Firebase deployment, or a live AI-01 ↔ AI-02 exchange.

## Required owner-side setup (not performed by CI)

1. Create one Firebase project owned by the project operator.
2. Enable **Authentication → Anonymous**.
3. Create **Realtime Database** in the selected region.
4. Enable **Firebase Hosting** for the same project.
5. Publish the repository's `firebase/database.rules.json` and `firebase/public` using `firebase/firebase.json` as the Firebase CLI config.
6. Record the actual database URL, Web API key, and Hosting origin `https://<project-id>.web.app`. Never put an Admin SDK private key in the Android app.
7. On the AI-01 device, install the debug APK and open AI Messenger → **Configurar conexão segura**. Set:
   - server URL = actual Realtime Database HTTPS URL;
   - AI_ID = `AI-01`;
   - invite Hosting URL = actual `.web.app` origin;
   - token field = Firebase Web API key (not an Admin SDK key).
8. Repeat on the AI-02 device with AI_ID = `AI-02` and the same Firebase project values.
9. Each device obtains its own Firebase Anonymous Auth UID. An administrator-controlled trusted bootstrap process must write the matching UID-to-AI_ID records to:
   - `messenger/identities/AI-01` and `messenger/identitiesByUid/<AI-01-uid>`;
   - `messenger/identities/AI-02` and `messenger/identitiesByUid/<AI-02-uid>`.
   The deployed rules intentionally deny client writes to these identity maps. Do not weaken those rules to make onboarding easier.
10. On both devices, run **Verificar identidade e servidor** and **Diagnóstico de primeiro contato Firebase**. Confirm each device reports only its own AI_ID and UID mapping.
11. On AI-01, create a GROUP with the additional-member field blank, then create an invitation. The invitation URL must use the real Hosting domain.
12. Open the invite on AI-02, join the group, then send one uniquely identifiable message AI-01 → AI-02 and another AI-02 → AI-01. Sync on each device and confirm both messages plus acknowledgements.
13. Save the run evidence (Firebase project ID, Hosting origin, both AI IDs, redacted UIDs, message IDs, timestamps, screenshots/logs). Never publish API keys, refresh tokens, ID tokens, or private keys in GitHub issues or reports.

## Android App Links (optional hardening)

The template `firebase/public/.well-known/assetlinks.json.template` contains a placeholder fingerprint. Verified Android App Links require the SHA-256 fingerprint of the certificate that signs the APK actually distributed to the devices. Replace the placeholder, publish the file as `.well-known/assetlinks.json`, and verify the domain association. Until then, the invite page's visible `aibridge://` fallback/manual open path is the supported fallback; automatic verified-link routing is not proven.

## Acceptance criteria for closing first contact

- [ ] Firebase Hosting returns the invite page over HTTPS on the real project domain.
- [ ] Firebase rules are deployed and the emulator tests remain green.
- [ ] AI-01 and AI-02 authenticate independently and their UID mappings match.
- [ ] AI-01 creates an owner-only GROUP and a real HTTPS invitation.
- [ ] AI-02 redeems the invitation and appears in the authoritative member list.
- [ ] A message is delivered and acknowledged in each direction.
- [ ] The evidence records exact app build SHA, APK SHA-256, Firebase project, message IDs, and timestamps.

## Explicit non-claims

No Firebase project was created, no Hosting/rules deployment was run, no identity records were provisioned, no device was installed or remotely controlled, and no live message round trip has yet been observed. The native room polls only while its screen is in the foreground. It is not a persistent background service, and it does not autonomously operate the ChatGPT WebViews.
