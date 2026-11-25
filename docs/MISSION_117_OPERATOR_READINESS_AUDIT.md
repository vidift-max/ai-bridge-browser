# Mission 117 — Operator Readiness & Staging Configuration Audit

## Ten-round execution record

1. Confirmed M116 final CI run 45543907867 was SUCCESS on HEAD 408c604d9273ffab74d20e9d092a1e6c991aa573; PR #116 remains Draft/open/unmerged.
2. Audited the staging Blueprint and found that operator readiness needed a separate offline check for plan, region, manual deploy, ephemeral memory storage, no disk, health check, fixed AI identities and private secret declarations.
3. Added `scripts/verify_staging_operator_readiness.py` to inspect the checked-in Blueprint without contacting Render.
4. The Blueprint audit requires Free/Oregon, `autoDeployTrigger: off`, ephemeral storage, `:memory:`, staging opt-in, AI-01/AI-02, `/healthz`, no disk/mount, and per-secret `sync: false`.
5. Hardened secret declaration inspection so each credential is independently required to have its own `sync: false`; one credential's setting cannot satisfy the other.
6. Added environment validation for both nonempty, distinct bearer credentials, fixed identities, staging mode, ephemeral opt-in, and in-memory database path. Values are never printed.
7. Added a deliberate pre-activation boundary: the audit returns NO_GO if staging/execution authorization flags or any exact approval binding are present. A successful report always states `authorization=NOT_GRANTED`.
8. Added seven focused tests for the repository Blueprint, per-secret sync policy, paid-plan/disk/autodeploy regressions, complete synthetic environment, missing/wrong configuration, duplicate credentials and accidental authorization flags.
9. Updated CI to run the M117 suite and compile the new script; repaired branch coverage so both M116 and M117 appear in push and pull_request filters, and removed a duplicate py_compile entry.
10. Prepared this operator runbook. No Render service, deploy, secret, network request, real message, paid resource, merge or physical activation was created or performed.

## Operator use

Run from the repository root after the operator has privately configured the eight required environment variables:

```sh
python scripts/verify_staging_operator_readiness.py
```

The command reads `render.staging.yaml` and the current process environment. It does not print token values, contact Render, perform a health check, deploy, or send a message.

Expected safe outcomes:

- `PASS`: Blueprint and operator environment match the audited staging contract; this is not deployment or execution authorization.
- `NO_GO`: one or more required settings are absent or invalid. The `failures` list contains variable/check names only, never secret values.

The command must run before any execution approval variables are configured. It intentionally rejects:
- `MESSENGER_FIRST_CONTACT_STAGING_AUTHORIZED`
- `MESSENGER_FIRST_CONTACT_EXECUTE`
- `MESSENGER_FIRST_CONTACT_APPROVED_ORIGIN`
- `MESSENGER_FIRST_CONTACT_APPROVED_CONVERSATION_ID`
- `MESSENGER_FIRST_CONTACT_APPROVED_OPERATION_ID`

## Staging constraints

- Render plan: Free; region: Oregon.
- Manual deployment only; no automatic deploy on commit.
- No persistent disk or mount. SQLite `:memory:` is temporary and non-durable.
- Two distinct credentials are configured manually and privately.
- This audit is offline and does not establish that a Render service exists, is reachable, or is healthy.
- A PASS does not grant permission to deploy or to send the first message. User authorization remains a separate conversational requirement.
- HTTP Long Poll remains the sole realtime transport; WebSocket/SSE remain disabled.
