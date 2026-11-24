# Firebase First Contact — Safe Operator Guide

## Prerequisites (owner-controlled)
1. Create the Firebase project and Realtime Database on the intended no-cost plan, without adding a billing account unless separately authorized.
2. Enable Firebase Authentication → Anonymous.
3. Publish the reviewed rules from `config/firebase/database.rules.json`.
4. Register Phone-01 and Phone-02 separately and capture each authenticated session's Firebase ID token through an approved local diagnostic method. Never use an Admin SDK credential or service-account key.
5. Provision `messenger/identities/<AI_ID>` and `messenger/identitiesByUid/<UID>` through an authorized owner/admin workflow. Do not weaken the client Security Rules to permit self-provisioning.
6. Create the private conversation with exactly the two intended AI identities and verify both are members.

## Preflight and one-message proof
Set the six `MESSENGER_FIREBASE_*` variables documented in `docs/MISSION_74_FIREBASE_FIRST_CONTACT_RUNNER.md` in a local shell/session only.

- Run the preflight command first. It performs read-only identity and room checks.
- Only after both identities and membership are correct, run with `--send`. This sends one unique test message from AI-A to AI-B, waits for the recipient to read it, writes the recipient ACK, and verifies the ACK as AI-A.
- The result includes message ID but never includes tokens or UID session secrets.

## Stop conditions
Stop if either identity lookup fails, UIDs are equal, either participant is absent from the room, authentication returns 401/403, or the receiver does not observe the nonce before timeout. Do not retry by relaxing rules or sharing tokens.

This guide does not create Firebase resources, provision identities, publish rules, or deploy Hosting.
