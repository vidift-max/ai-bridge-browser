# Mission 50 — Authenticated provider session binding

## Objective

Make the browser-session adapter consume the result of the provider handshake as an explicit, session-scoped authorization boundary. A successful handshake must not grant capabilities to another session, provider, or origin.

## Ten rounds

1. Confirmed Mission 49 PASS on exact SHA b68d699ed4018705f3e8631e71c578418673a524; all three CI jobs succeeded.
2. Audited the existing session adapter and provider handshake contracts.
3. Identified that tab registration accepted only a boolean consent flag and did not require a verified handshake result.
4. Identified that provider adapter methods were exposed as capabilities without intersecting them with the handshake's host-granted actions.
5. Identified asynchronous completion races where a tab closed during connect or send could still receive a misleading success state/result.
6. Created an isolated branch from the verified Mission 49 head.
7. Required an authenticated, unexpired handshake bound exactly to session ID, provider ID, and HTTPS origin before tab registration.
8. Enforced the handshake capability grant independently of adapter method availability for status reads, message sending, and reconnect requests.
9. Added close-during-connect and close-during-send protections plus regression tests for missing, expired, mismatched, duplicate, unknown, and insufficient grants.
10. Added a dedicated CI workflow and this evidence document; PR remains Draft pending complete CI on the final SHA.

## Enforced contract

- Tab registration requires explicit user consent and a verified handshake result.
- Handshake status must be AUTHENTICATED.
- Session ID, provider ID, and normalized HTTPS origin must match exactly.
- Handshake expiry is checked using now >= expiresAt.
- Capabilities must be non-empty, unique, and from READ_STATUS, SEND_MESSAGE, REQUEST_RECONNECT.
- The effective session capabilities come from the handshake grant, not from the provider adapter's available methods.
- An action requires both a handshake grant and an available adapter method. Message/reconnect actions additionally require the existing explicit host authorization callback.
- Async connect, status, send, and reconnect completions check that the same session remains active before reporting success.
- Session metadata and audit records continue to exclude provider tokens and message bodies.

## Limitations

- The handshake object is expected to be produced by the trusted host after cryptographic proof verification. This adapter does not independently verify signatures or provider ownership.
- The adapter remains a host-side integration contract; it does not automate browser login, inspect arbitrary tabs, or bypass provider security controls.
- No real ChatGPT, Claude, Gemini, OAuth account, remote device, or external browser was connected.
- No paid API, merge, or deployment was activated.
- CI success will prove automated regression behavior only, not a live provider connection.

## Validation

node --test web/ai-session-adapter.test.mjs

The mission workflow also runs full backend, browser, and Android regression suites on the exact final commit.
