# Mission 111 — First-contact idempotency and duplicate-send protection

## Ten-round execution record

1. Confirmed M110 CI SUCCESS on run 45541670386, including backend, browser, activation-boundary and Android jobs.
2. Audited the first-contact runner's message identifiers and found they were newly randomized for every invocation.
3. Identified the ambiguous-timeout hazard: a server may accept a POST even if the client does not receive its response; a fresh rerun would otherwise use a different idempotency key.
4. Added a required CLI environment value, `MESSENGER_FIRST_CONTACT_OPERATION_ID`, for real execution.
5. Added strict operation-ID validation: 16–128 ASCII characters from letters, digits, dot, underscore and hyphen; invalid values fail before any network request.
6. Derived both `messageId` and `clientRequestId` deterministically from SHA-256 of the operation ID, so a deliberate retry with the same operation ID reuses the same pair.
7. Ensured raw operation IDs are not embedded in generated message identifiers or success output.
8. Added regression tests for stable IDs, different IDs, invalid values, pre-network rejection and non-disclosure.
9. Updated M110 CLI gate tests and registered M111 tests/branch filters in the CI workflow.
10. Documented the operator rule: preserve the same operation ID when recovering an ambiguous attempt; never create a new ID merely because a request timed out.

## Operator rule

Set `MESSENGER_FIRST_CONTACT_OPERATION_ID` to a unique, non-secret operation label of 16–128 allowed characters before execution. Keep that exact value for any recovery attempt related to the same intended first contact. The runner hashes it into stable `messageId` and `clientRequestId` values. Do not invent a new operation ID after an ambiguous timeout.

The backend implementation already indexes idempotency by authenticated sender plus `clientRequestId`: an identical replay returns the original message, while reuse with different message content/recipients is rejected as an idempotency conflict. Existing backend regressions cover conflict rejection and concurrent identical submissions. M111 adds `server.test_messenger_backend` to this mission's CI command so that server-side contract is exercised alongside the stable client identifiers. This is source/CI evidence, not proof against a live deployed service. The runner does not automatically retry a failed or ambiguous POST.

## Evidence and safety boundary

M110's CI was SUCCESS before this mission began. M111's CI must pass before this mission can be called validated. No Render deployment, live credentials, real message, paid resource, physical device activation or merge was performed. HTTP Long Poll remains the only realtime transport; staging remains Free, ephemeral and manual-deploy only.
