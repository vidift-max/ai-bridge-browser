# Mission 115 — First Contact Final Preflight & Deployment Checklist

## Ten-round execution record

1. Confirmed M114 CI run 45543197303 was SUCCESS on HEAD a2911841493275f99a258a74e6dad4714ac62af6; PR #114 remains Draft/open/unmerged.
2. Audited the existing first-contact runner, offline configuration validator, staging authorization gate, health/readiness verifier and Free staging Blueprint.
3. Added `scripts/verify_first_contact_preflight.py`, an offline final preflight that validates the HTTPS origin, conversation ID, fixed AI identities, distinct credentials, staging environment, ephemeral storage, in-memory DB and stable operation ID.
4. Kept preflight deliberately separate from execution authorization: it does not require or set either execution gate and always reports `network=NOT_CONTACTED`, `realContact=NOT_AUTHORIZED`, `execution=NOT_STARTED`.
5. Ensured preflight output omits the staging hostname, bearer credentials and operation ID; it reports only categorized check results.
6. Hardened `verify_staging_http.py` to expose only an allowlisted `status` value and HTTP status code, replacing arbitrary upstream bodies with generic errors.
7. Added tests proving valid offline readiness, wrong environment/storage rejection, invalid operation ID rejection, missing/duplicate credential rejection and no execution authorization.
8. Added verifier regression tests proving that arbitrary health/readiness fields and HTTP error bodies (including secret-like values) are not returned.
9. Registered M115 tests, Python compilation and branch filters in the existing CI workflow.
10. Prepared the operator checklist below; no Render service, deployment, secret, real message, paid resource or physical activation was created or used.

## Operator checklist — before any real first contact

- [ ] Confirm the intended staging service is the Free plan in Oregon.
- [ ] Confirm `autoDeployTrigger: off`; deployment must remain manual.
- [ ] Confirm no persistent disk is attached.
- [ ] Confirm `MESSENGER_ENVIRONMENT=staging`.
- [ ] Confirm `MESSENGER_ALLOW_EPHEMERAL_STAGING=true`.
- [ ] Confirm `MESSENGER_STORAGE_MODE=ephemeral` and `MESSENGER_DB_PATH=:memory:`.
- [ ] Configure two distinct bearer credentials privately as `MESSENGER_TOKEN_AI_A` and `MESSENGER_TOKEN_AI_B`; never put them in Git, issue comments, logs or chat.
- [ ] Confirm identities are exactly AI-01 and AI-02.
- [ ] Confirm an approved conversation ID and a stable operation ID (16–128 characters from A–Z, a–z, 0–9, dot, underscore or hyphen).
- [ ] Run the offline preflight: `python scripts/verify_first_contact_preflight.py https://<staging-origin> <conversation-id>`.
- [ ] Only after explicit operator approval, deploy manually and run the read-only health verifier: `python scripts/verify_staging_http.py https://<staging-origin>`.
- [ ] Review `/healthz` and `/readyz` status without exposing raw service responses.
- [ ] Obtain a separate, explicit approval in the conversation before setting `MESSENGER_FIRST_CONTACT_STAGING_AUTHORIZED=true` and `MESSENGER_FIRST_CONTACT_EXECUTE=true`.
- [ ] Only then consider the real first-contact command, with `--execute`, the approved conversation ID and the stable operation ID.
- [ ] Verify AI-01 identity, AI-02 identity, QUEUED, Long Poll receipt, ACKNOWLEDGED and post-ACK pending removal. Stop on any mismatch or ambiguous result.

## Boundaries and cautions

- The offline preflight PASS is not evidence that Render exists, is deployed, is reachable or is healthy.
- Health/readiness checks make network GET requests but do not authenticate, send messages or modify service state.
- The real first-contact runner performs network operations and must never be launched as part of preflight.
- Free ephemeral SQLite memory storage is temporary and may be lost on restart/redeploy; this is not production durability.
- No automated workflow deploys staging. The existing workflow only runs tests and asserts the staging Blueprint boundary.
- HTTP Long Poll remains the only realtime transport. WebSocket and SSE remain disabled.
- This mission does not prove a real AI-01 → AI-02 exchange or physical Phone-02 activation.
