# Mission 12 — AI Remote Control & Continuity Supervisor

## Goal
Add a policy-gated control-plane core for authenticated AI Bridge session adapters. This is not proof that an external ChatGPT/Gemini/Claude account or physical device is connected.

## Ten rounds
1. Audited the Mission 11 WebRTC client and confirmed it only handles call signaling, not general remote session control.
2. Created an isolated branch from `feat/mission-11-webrtc-reliability`; parent PRs were not merged or retargeted.
3. Defined a narrow allowlist: `SEND_MESSAGE`, `REQUEST_RECONNECT`, `READ_STATUS`. Arbitrary JS, shell commands, navigation, and arbitrary URLs are unsupported.
4. Implemented short-lived, session-bound grants with explicit action scopes, expiry, revocation, and bounded use counts.
5. Added action-ID idempotency to prevent retry side effects.
6. Added an authenticated adapter boundary; missing capabilities fail closed.
7. Added heartbeat observation and stale-session detection, distinguishing observed CONNECTED from inferred OFFLINE/UNKNOWN.
8. Added bounded reconnect supervision with exponential backoff, attempt limits, and reset after a fresh heartbeat.
9. Added structured audit events with a field allowlist; message bodies, credentials, SDP and adapter secrets are excluded.
10. Added ten deterministic Node tests for authorization, expiry, session binding, limits, idempotency, input validation, audit privacy, heartbeat freshness, recovery/backoff, revocation, and shutdown.

## Integration contract
A future host must supply an authenticated adapter exposing only capabilities it is authorized to provide. The control plane does not store credentials, obtain OAuth tokens, bypass provider controls, or manufacture AI identity. Grant issuance remains a trusted server/operator decision, never untrusted page input.

## State semantics
- CONNECTED means a valid heartbeat was observed.
- OFFLINE means an observed heartbeat exceeded the configured freshness threshold.
- UNKNOWN means no heartbeat evidence exists.
- A reconnect request is only an attempt; a fresh heartbeat is required to restore CONNECTED.

## Safety and limits
- No arbitrary code execution, shell access, unrestricted browser navigation, or unbounded message sending.
- Grant TTL is capped at 15 minutes and use count is bounded.
- This is a reusable policy engine, not yet wired to a production browser-control adapter or provider connector.
- No external AI account, remote tab, phone, microphone, WebRTC call, or cross-network recovery was exercised.
- No paid service, credential, infrastructure, merge, or deployment was activated.

## Validation
Run `node --test web/ai-control-plane.test.mjs`. Tests use a fake adapter and deterministic clock; they prove local policy behavior only.
