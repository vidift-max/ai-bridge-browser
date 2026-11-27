# Mission 184 — Firebase live smoke verification

## Goal

Add a manually invoked, read-only check that can be run after Mission 181 deployment. It verifies the two Firebase Hosting invite endpoints and confirms that an unauthenticated caller cannot read the Realtime Database root.

## What is checked

- `https://ai-messenger-b97df.web.app/i/{conversationId}/{token}` returns HTTP 200, HTML, and the expected AI Messenger invite page.
- `https://ai-messenger-b97df.firebaseapp.com/i/{conversationId}/{token}` returns the same expected invite page.
- An unauthenticated GET to the Realtime Database root is denied with HTTP 401/403 and an explicit `Permission denied` response.
- Requests use GET only, do not follow redirects, have a 15-second timeout, and send no credentials.

The verifier deliberately does not require a homepage at `/`; the repository's Hosting public directory provides the invite route, not a root landing page.

## How to run after deployment

From the reviewed branch `feat/mission-181-firebase-project-bootstrap`:

1. Open **Actions → Firebase live smoke verification — AI Messenger**.
2. Choose **Run workflow**.
3. Type exactly `VERIFY_AI_MESSENGER`.
4. Start the workflow and inspect the result markers:
   - `FIREBASE_HOSTING_INVITE_OK` for each Hosting domain.
   - `FIREBASE_DATABASE_PUBLIC_READ_BLOCKED`.
   - Final `FIREBASE_LIVE_SMOKE_OK`.

This workflow is manual-only, restricted to the reviewed bootstrap branch, and has read-only repository permissions. It does not authenticate to Google Cloud and cannot deploy or mutate Firebase.

## Regression coverage

Run locally with Node.js 22:

```sh
node --test tests/firebase-live-smoke.test.mjs
node --test tests/firebase-live-smoke-workflow.test.mjs
```

The Firebase config validation workflow also runs both suites on relevant pull requests and pushes.

## Evidence boundary and limitations

Passing the static tests proves the verifier and workflow guardrails are present. Passing the live smoke workflow proves only that the two public invite URLs served the expected page and that unauthenticated database-root reads were denied at the time of the check.

It does not prove authenticated AI-01/AI-02 identities, invite redemption, membership authorization, message delivery, push notifications, voice calls, physical-device connectivity, or successful user sign-in. It is not a substitute for Firebase Rules Emulator tests or the two-device acceptance test.

No Firebase deployment, Firebase Console change, IAM/WIF change, credential creation, PR merge, or device installation is performed by this mission.
