# Mission 126 — Invite Link Entry Hardening and Shared Group Room

## Objective
Harden the Android deep-link entry used by AI Messenger group invitations and verify that the browser Rooms page keeps multiple participants inside one selected group conversation. The invitation link is the entry point; it does not create one browser tab per AI.

## Ten work rounds
1. Audited the M125 baseline and confirmed all four CI jobs passed before opening this mission.
2. Traced the existing browser Rooms UI: one selected conversation owns one participant directory, one message timeline, and one composer.
3. Confirmed GROUP conversations support multiple selected participants (up to the existing 20-member server-side room bound).
4. Audited the web invite flow: secret is carried in the URL fragment, removed from browser history, and guest entry is a request pending administrator approval.
5. Audited the Android manifest deep-link declarations for the `aibridge://invite` and HTTPS Firebase Hosting invite routes.
6. Added a strict platform-independent invite URI parser with explicit scheme, host, path, query, fragment, user-info, port, identifier, and token validation.
7. Replaced the permissive inline Android URI parser with the shared strict parser before any redemption request.
8. Added JVM regression tests for valid URI forms, case handling, malformed paths, host spoofing, user-info, ports, query/fragment injection, encoded path separators, identifier bounds, and token boundaries.
9. Added browser contract tests proving one shared group conversation, multi-participant selection, room-scoped invitations, fragment secrecy, approval-gated guest entry, and native deep-link routing.
10. Added this evidence record and wired the mission into CI; no merge, deployment, real invite redemption, or external AI contact was performed.

## Evidence boundaries
- The browser Rooms page and native collective-room activity are existing implementations; this mission hardens invite parsing and adds regression coverage rather than claiming to create the group chat from scratch.
- Browser invite requests require administrator approval; the native Firebase group-invite route redeems a room-scoped invite before opening the collective room.
- A single group conversation contains multiple participants. This does not mean multiple independent AI provider sessions are authenticated or actively responding.
- No Render service, Firebase deployment, real invitation, physical device test, real AI-to-AI message, or ACK was performed.
