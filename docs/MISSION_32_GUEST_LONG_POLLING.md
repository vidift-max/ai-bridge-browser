# Mission 32 — Guest Long Polling

## 10 rounds
1. Revalidated Mission 31 CI as successful before starting the next mission.
2. Audited the existing authenticated message and acknowledgement contracts.
3. Added a server-side condition-backed wait primitive without changing room authorization.
4. Bounded long-poll timeout to a maximum of 25 seconds.
5. Reused the existing pending-message cursor and acknowledgement model.
6. Notified waiting clients immediately after a new message is persisted.
7. Added an authenticated HTTP endpoint at `/v1/conversations/{conversationId}/messages/wait`.
8. Switched the guest browser messenger from fixed request polling to long polling while retaining visibility and bounded retry behavior.
9. Added backend and browser regression tests for immediate delivery, timeout, wake-up, invalid timeout, and route usage.
10. Added dedicated Mission 32 CI and documented proof boundaries.

## Security and proof boundaries
- Existing bearer/session authentication and single-room authorization remain mandatory.
- No new privilege path, provider verification, or external AI automation.
- No WebSocket implementation is claimed.
- Long polling is still HTTP request/response transport.
- No deployment or physical-device validation is claimed.
- Paid APIs, model downloads, and inference remain outside this mission.

## Acceptance
PASS requires the Mission 32 CI workflow to complete successfully on the final SHA.
