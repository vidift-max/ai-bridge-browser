# Mission 128 — Web Invite Link to Single Browser Tab

## Objective
Align Android app-link handling with the actual invite URL emitted by the Rooms web UI, and open that invite page inside the existing AI Bridge Browser tab.

## Ten rounds
1. Confirmed M127 CI 4/4 SUCCESS and its PR remains Draft/unmerged.
2. Audited the Rooms invite generator: it emits `https://<host>/invite#<inviteId>.<token>`.
3. Audited `invite.html`: it reads the fragment, removes it from browser history, and submits a guest application; approval and provisioning are still required.
4. Identified the mismatch: the native deep-link parser/manifest handled `/i/<room>/<token>` and `aibridge://`, not the actual web `/invite#...` URL.
5. Added a dedicated parser for the actual web invite route, restricted to HTTPS Firebase Hosting hosts and the exact `/invite` path.
6. Added validation for fragment shape, invite ID/token character sets and lengths, and rejection of credentials, ports, query strings, encoded fragments, and unrelated hosts.
7. Connected MainActivity launch and `onNewIntent` handling to the validated invite URL; the existing selected WebView loads it.
8. Registered the web invite app-link route on MainActivity with `singleTop`; retained the legacy native invite activity for its distinct route.
9. Added browser contract tests tying together the Rooms URL generator, invite page fragment handling, manifest route, and same-WebView navigation.
10. Added this evidence record and wired the mission branch/test into CI.

## Security and evidence boundaries
- The fragment token is passed only to the existing invite page; this Android handoff does not redeem it or grant room membership.
- The invite page removes the fragment from history and submits an approval-gated guest application.
- Android App Links require a valid `/.well-known/assetlinks.json` on the actual hosting domain for verified automatic association. This mission does not deploy or claim that association file exists.
- The app-link host filter is Firebase Hosting `*.web.app`; custom domains need a separately reviewed manifest/domain association.
- No real invitation, guest application, external AI message, ACK, Render/Firebase deployment, physical installation, or merge was performed.
