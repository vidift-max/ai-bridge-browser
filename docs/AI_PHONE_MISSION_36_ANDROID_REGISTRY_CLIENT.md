# Mission 36 — Android AI-PHONE registry connection

Status: IMPLEMENTATION COMPLETE — FINAL CI GATE PENDING
Repository: `vidift-max/ai-bridge-browser`
Branch: `v2-saas-alpha`

## Goal

Connect the Android Home screen to the authenticated server-side AI-PHONE registry so an authorized AI participant can retrieve and see the number assigned to its own authenticated AI_ID. The app must not invent numbers or treat a local profile as an authenticated identity.

## Ten completed rounds

1. **Architecture audit:** traced the server `GET /v1/me/phone` contract, Bearer authentication, response schema, Android identity model and Home screen. Confirmed the app previously displayed only an unassigned placeholder.
2. **Connection validation:** added `AiPhoneRegistryConfig` to require HTTPS, reject user-info/query/fragment URL components, normalize trailing slashes and validate AI_ID before any network call.
3. **Credential protection:** added `AiPhoneCredentialVault`, encrypting the Bearer credential with AES-GCM and a key generated/stored by Android Keystore. Only ciphertext and IV are persisted in app-private preferences.
4. **Authenticated HTTP client:** added `AiPhoneRegistryClient` for `GET /v1/me/phone`, HTTPS only, Bearer header, JSON accept header, no HTTP cache, 10-second connect/read timeouts and bounded response size.
5. **Response validation:** parses the server phone record through `AiPhoneIdentity.fromRegistryRecord` and rejects a response whose AI_ID differs from the configured authenticated principal.
6. **Home screen settings:** added a connection dialog for server HTTPS URL, AI_ID and Bearer credential. It saves non-secret endpoint/principal settings and stores the credential through the Keystore vault.
7. **Live identity display:** replaced the fixed unassigned number/serial placeholders with fields updated only after a successful authenticated server response; errors remain visibly disconnected and do not fabricate a number.
8. **Restart behavior:** on Home screen creation, reuses the protected credential and re-queries the server rather than treating a stale local number as authoritative.
9. **Regression coverage and docs:** added JVM tests for HTTPS URL normalization/rejection and AI_ID validation; updated the identity registry contract with the Android client behavior and trust boundaries.
10. **CI acceptance:** run Android Build and backend tests on the exact final branch SHA. PASS requires both workflows to succeed; CI proves compilation/tests only, not deployment or a physical-phone connection.

## Changed files

- `app/src/main/java/com/vidiftmax/aibridgebrowser/AiPhoneRegistryConfig.java`
- `app/src/main/java/com/vidiftmax/aibridgebrowser/AiPhoneRegistryClient.java`
- `app/src/main/java/com/vidiftmax/aibridgebrowser/AiPhoneCredentialVault.java`
- `app/src/main/java/com/vidiftmax/aibridgebrowser/HomeActivity.java`
- `app/src/test/java/com/vidiftmax/aibridgebrowser/AiPhoneRegistryConfigTest.java`
- `docs/AI_PHONE_IDENTITY_REGISTRY.md`

## Boundaries

- The backend must be deployed and reachable over HTTPS, and the AI_ID must already have a valid configured Bearer credential.
- No credential, server URL, identity, or device is preconfigured by this source change.
- No physical Android device test has been performed.
- This does not yet connect AI Messenger conversations to remote participants, create a collective room, implement presence/push, or implement WebRTC voice calls.
- AI-PHONE numbers remain virtual ecosystem identifiers, not carrier/PSTN numbers.

## Acceptance

PASS only when Android Build and Messenger Backend Test are SUCCESS on the exact same final commit SHA. Live registry enrollment still requires a separately deployed and configured server.
