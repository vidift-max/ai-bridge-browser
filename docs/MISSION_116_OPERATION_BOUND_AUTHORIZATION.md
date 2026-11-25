# Mission 116 — Operation-Bound First-Contact Authorization

## Ten-round execution record

1. Confirmed M115 PR #115 remained Draft/open/unmerged and its final CI run 45543569323 was SUCCESS on HEAD 13fcd80d18f2b43dddecadd272427d8c5926d710.
2. Audited the runner's authorization call site and confirmed the previous two boolean gates were not bound to a specific staging origin, conversation or operation ID.
3. Added exact-origin binding through `MESSENGER_FIRST_CONTACT_APPROVED_ORIGIN`.
4. Added exact-conversation binding through `MESSENGER_FIRST_CONTACT_APPROVED_CONVERSATION_ID`.
5. Added exact-operation binding through `MESSENGER_FIRST_CONTACT_APPROVED_OPERATION_ID`, with the same 16–128 character safe alphabet used by the idempotency key.
6. Changed the execution CLI to normalize the HTTPS origin and validate all approval bindings before calling `run_first_contact`; no identity GET, Long Poll, message POST or ACK can happen before this gate passes.
7. Added negative tests for stale/wrong origin, conversation and operation approvals, malformed/missing bindings, and missing staging/execution gates.
8. Updated the existing execution-safety regression to prove an approval for a different operation cannot reach the network runner.
9. Registered the M116 tests, Python compilation and branch filters in CI.
10. Documented the operator boundary and exact environment bindings; no deployment, credentials, network contact, paid resource, merge or physical activation was performed.

## Required operator-supplied bindings

Alongside the existing staging/execution gates, the operator must deliberately configure:

- `MESSENGER_FIRST_CONTACT_APPROVED_ORIGIN`: exact normalized HTTPS origin, e.g. `https://<staging-host>`.
- `MESSENGER_FIRST_CONTACT_APPROVED_CONVERSATION_ID`: exact approved conversation ID.
- `MESSENGER_FIRST_CONTACT_APPROVED_OPERATION_ID`: exact 16–128 character operation ID used by this execution.

The CLI compares all three values to the command's actual origin, conversation and operation ID. A stale value or a value for a different target fails closed before the first HTTP request.

## Important authorization distinction

These environment values are a technical execution guard, not proof that the user approved an action in ChatGPT. Do not set them, or the existing `MESSENGER_FIRST_CONTACT_STAGING_AUTHORIZED=true` and `MESSENGER_FIRST_CONTACT_EXECUTE=true`, merely to make a test pass. Real execution still requires explicit, current user authorization in the conversation, followed by deliberate operator configuration and manual staging deployment.

## Existing safe staging constraints

- Render Free plan, Oregon, manual deploy only (`autoDeployTrigger: off`).
- No persistent disk; SQLite `:memory:` is ephemeral and non-durable.
- Distinct private bearer credentials for AI-01 and AI-02; never commit or log them.
- HTTP Long Poll is the only realtime transport; WebSocket/SSE remain disabled.
- Preflight is offline. This mission does not deploy or send a real message.
- No claim is made that Render exists, is healthy, or that Phone-02 is physically activated.
