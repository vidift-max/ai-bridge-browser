# Mission 72 — Call and Invitation Notifications

## Goal
Extend the existing per-AI notification center to surface incoming 1:1 calls, pending room-join requests, and redemption of room invitations. No action is performed automatically.

## Ten rounds
1. Verified Mission 71 PR #70 remains open, Draft, and unmerged; based this mission on its latest documented HEAD.
2. Inspected authenticated call-active, join-request, and room-invite endpoints and existing UI flows.
3. Added a dedicated event monitor with per-session deduplication for incoming ringing calls.
4. Added deduplicated notifications for newly pending room-join requests.
5. Added notifications when an existing room invite's usage count increases.
6. Extended local notification records with typed title/detail metadata while preserving existing message records.
7. Added a browser-served event-monitor script and an explicit GET route.
8. Integrated bounded polling into the authenticated Rooms session and reused Mission 71 per-AI category/browser preferences.
9. Added focused event-monitor tests and an HTTP route contract test.
10. Added a dedicated CI workflow and this mission report; final CI results are recorded after execution.

## Behavior and safety
- Incoming call checks cover at most 12 loaded private 1:1 rooms per poll; polling interval is 30 seconds.
- Join-request and invite-use checks cover at most 8 loaded group rooms per poll and require existing room-admin authorization. Non-admin 401/403 responses are ignored.
- First observations establish a baseline; only subsequent new calls, pending requests, or increases in invite use generate alerts.
- Duplicate events are suppressed during the session.
- Notifications never auto-answer calls, request microphone access, approve/reject requests, redeem invites, or change room membership.
- Existing PRIVATE/GROUP notification preferences and browser-permission rules apply.
- Events are stored in the local notification center and can open the relevant conversation.
- Invitation use indicates that the invitation was redeemed/used; it does not identify a human or assert that an invitee was approved.
- No server push transport was added. HTTP Long Poll remains the only enabled realtime transport; this feature uses bounded authenticated polling.

## Verification
- Workflow run `45469868266`: SUCCESS on the implementation/documentation HEAD `204a9f3a060988aca463980efc292b1702617263`.
- Browser Regression: 280/280 tests PASS.
- Backend Regression: 473 tests PASS, including `test_room_event_notification_script_route_is_defined`.
- Both jobs completed successfully.

## Limits
Monitoring covers currently loaded conversations only. Admin-only room endpoints may return 403 and are intentionally ignored. No merge or deployment is performed.
