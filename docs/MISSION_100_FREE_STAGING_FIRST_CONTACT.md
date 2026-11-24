# Mission 100 — CI validation and free staging readiness for AI-01 → AI-02

## Ten-round execution record

1. Recovered M99 workflow run #33 (`45496232341`) and verified terminal conclusion SUCCESS.
2. Verified all four CI jobs: backend-invite-e2e, android-regression, browser-invite-contract, activation-boundary — all SUCCESS.
3. Rechecked PR #98: Draft, open, unmerged, mergeable; M99 head `294565d3bbfe8267254877a0d8050f73b62a1c8d`.
4. Audited the staging health/readiness route and found a configuration contradiction: the Free staging Blueprint selected `MESSENGER_STORAGE_MODE=ephemeral`, while runtime readiness unconditionally rejected ephemeral storage.
5. Confirmed the operational consequence: even a manually started Free instance would fail `/readyz`; no first-contact session could pass the documented preflight.
6. Implemented a fail-closed opt-in: ephemeral storage is accepted only when `MESSENGER_ENVIRONMENT=staging` AND `MESSENGER_ALLOW_EPHEMERAL_STAGING=true`; default and production remain rejected.
7. Added runtime-config tests for default rejection, production rejection, explicit staging acceptance, and invalid flag rejection.
8. Updated the Free staging Blueprint with the two explicit staging-only environment values; kept Free plan, in-memory DB, no disk, and manual deploy trigger.
9. Extended the staging-boundary test and CI workflow to run runtime config tests and assert the opt-in values; added the M100 branch to push and PR triggers.
10. Prepared the first-contact runbook and recorded the authorization boundary: no service activation, no secret creation, no deployment, and no real AI sessions initiated.

## First-contact protocol (only after explicit staging authorization)

1. Confirm the staging service is created on Free and manually deployed by the owner. Do not create or deploy it as part of this PR.
2. Configure two distinct, high-entropy bearer credentials privately as `MESSENGER_TOKEN_AI_A` and `MESSENGER_TOKEN_AI_B`. Never put values in Git, logs, issue comments, or this document.
3. Keep identities fixed as `MESSENGER_AI_ID_A=AI-01` and `MESSENGER_AI_ID_B=AI-02`; verify each credential independently through `GET /v1/me/identity`.
4. Verify `GET /healthz` and `GET /readyz`; verify both identities can access only their authorized conversation.
5. From the AI-02 session, start `GET /v1/conversations/<conversationId>/messages/wait?after=0&limit=10&timeout=25` using only AI-02's token.
6. From the AI-01 session, submit `POST /v1/messages` with messageId, conversationId, recipientAiIds=[AI-02], body, clientRequestId. Do not supply or spoof a sender identity.
7. Confirm the response is QUEUED and the Long Poll response identifies sender AI-01, recipient session AI-02, the same message ID and body.
8. From AI-02 only, acknowledge with `POST /v1/messages/<messageId>/ack`; require HTTP 200 and state ACKNOWLEDGED.
9. Repeat pending read and confirm the acknowledged message is no longer pending; record redacted timestamps, message ID, correlation IDs, and HTTP statuses.
10. Stop the test; revoke both credentials and delete/recreate the ephemeral service if needed. Do not treat ephemeral storage as durable or use it for production data.

## Free-tier and data-loss boundary

The M100 Blueprint remains Free and uses SQLite `:memory:` with no persistent disk. Messages, credentials, and room state are transient and may disappear on process restart, instance replacement, or redeploy. This is acceptable only for a short, controlled first-contact proof. It is not production durability. The opt-in does not add a paid resource and does not enable ephemeral storage in production by default.

## Evidence and status

- M99 CI run #33: `45496232341` — SUCCESS, all four jobs SUCCESS.
- M99 PR #98 remains Draft/open/unmerged.
- M100 branch base: `294565d3bbfe8267254877a0d8050f73b62a1c8d`.
- CI on M100: pending.
- Real independent AI-01 ↔ AI-02 message + ACK: NOT YET TESTED.
- Render service activation/deployment: NOT AUTHORIZED and NOT PERFORMED.
- No credentials were created, copied, or exposed.
- No physical device activation, merge, paid plan, persistent disk, or payment information.
