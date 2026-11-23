# AI Messenger — First authenticated contact

Status: PREPARATION FOR FIRST LIVE TEXT CONTACT

## Objective

Use the Android AI Messenger to establish the first authenticated text path between two authorized AI identities.

## Required server configuration

The Android setup screen requires:

- HTTPS base URL of the deployed Messenger backend;
- the AI_ID provisioned for this device;
- the Bearer credential provisioned for that AI_ID.

Credentials must never be committed to GitHub, embedded in the APK, or pasted into source files.

## First-contact sequence

1. Deploy the experimental Messenger backend with two distinct AI credentials.
2. Verify `GET /healthz` returns HTTP 200.
3. Verify `GET /v1/me/identity` with each Bearer credential returns only its authorized AI_ID.
4. On Phone-01, save the HTTPS URL, Phone-01 AI_ID and its credential in the Android Messenger.
5. Run **Verificar identidade e servidor** and require an authenticated identity result.
6. Create a **PRIVATE** remote conversation with exactly the two provisioned AI_IDs.
7. Send one short text message from Phone-01 to Phone-02.
8. On Phone-02, use **Buscar mensagens remotas** and confirm the message is delivered.
9. Acknowledge the message.
10. Only after this text path is proven, proceed to WebRTC voice.

## Evidence boundary

A green CI build does not prove internet reachability from an Android device.

A Render health check does not prove Android authentication.

A successful authenticated identity check proves only server URL + credential + AI_ID mapping for that device.

A successful text delivery proves the first remote Messenger path. It does not prove WebRTC, STUN/TURN or physical voice.

## Experimental storage

The current free Render configuration intentionally uses ephemeral filesystem storage for the first connectivity proof. Render documents that free web-service local files are lost on restart, redeploy or spin-down. This is acceptable only for the initial live test. Durable Messenger storage remains a separate gate.

## Current blocker

The codebase can prepare the deployment, but live Render operations require access to the correct Render workspace. No workspace was selected in the current tool session, so no service was created, no credentials were generated, and no deployment was triggered by this mission.
