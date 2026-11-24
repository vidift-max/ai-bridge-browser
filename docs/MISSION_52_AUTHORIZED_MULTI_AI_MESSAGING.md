# Mission 52 — Authorized multi-AI room messaging

## Objective
Connect the Mission 51 room membership contract to message send/receive authorization. Every message operation must be tied to an active room, an active AI identity, and the current session; inbound sender identity is resolved from authoritative room membership rather than trusting message-supplied session claims.

## Ten rounds
1. Verified Mission 51 final SHA `e09879178a32065f764ade4a7ec940ced444103e`; Backend, Browser, and Android workflows all passed.
2. Audited existing guest-room message payload, HTTP Long Poll delivery, acknowledgement, and room admission interfaces.
3. Defined the bridge contract between room membership and messenger callbacks; transport and UI remain separate.
4. Created branch `feat/mission-52-authorized-multi-ai-messaging` from the validated Mission 51 branch head.
5. Implemented outbound message construction gated by the admission service and current session binding.
6. Implemented recipient selection from active writable room members; observers are excluded and cannot send.
7. Implemented inbound validation using authoritative sender membership/session data, local recipient membership, and room scope.
8. Added post-transport and post-delivery authorization rechecks to prevent success after revocation; acknowledgement follows successful local delivery only.
9. Added duplicate acknowledgement handling, retry-safe delivery, body/sequence validation, and regression tests for spoofing, revocation, observer roles, and room closure.
10. Added documentation and Backend/Browser/Android CI; opened a Draft PR without merge or deployment.

## Security and behavior
- The host admission service is the source of truth for room membership and connected sessions.
- Sender session identity in an incoming message is never trusted; sender session is derived from the room membership record.
- Outbound and inbound message actions revalidate authorization after asynchronous boundaries.
- Observer participants are read-only: they may receive messages but cannot send them. The room admission API now exposes a separate `authorizeRead` check, while `authorizeMessage` continues to enforce write permission.
- Acknowledgement occurs only after successful local delivery; delivery failures remain retryable.
- Outbound recipient lists are derived from current active room membership, including observers as receive-only recipients.
- Duplicate deliveries are acknowledged idempotently and not delivered twice within the bridge instance.
- Membership does not grant provider API/tool access or arbitrary browser access.
- HTTP Long Poll remains the only enabled realtime transport; WebSocket and SSE remain disabled.

## Limitations
- This module is an integration seam around the existing host admission service and transport callbacks; it is not yet wired into the production page/server endpoint.
- Deduplication state is in-memory and process-local; durable idempotency belongs to the server message store.
- No real ChatGPT/Claude/Gemini account was connected and no physical AI phone was activated.
- No paid API, merge, or deployment was activated.

## Validation
`node --test web/ai-room-messenger.test.mjs`
