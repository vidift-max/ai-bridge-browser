# Mission 180 — Operational Readiness for the First Real Two-AI Test

## Scope

This mission prepares a controlled first test of two real AI identities. It does **not**
deploy, provision secrets, log into provider accounts, enable paid calls, activate
devices, create a room, register sessions, or contact a provider.

## Ten engineering rounds

1. Audit M179 exact SHA and CI evidence.
2. Audit the M178→M179 dependency chain.
3. Trace provider bootstrap, assignment and credential/policy sources.
4. Define a non-networking machine-readable preflight.
5. Validate explicit AI/provider assignments, including duplicate JSON keys.
6. Validate both required provider credentials and explicit call-policy switches.
7. Validate the 32-byte host HMAC prerequisite without exposing its value.
8. Define the operator checklist for the private two-member room and own-session registration.
9. Run deterministic server/browser CI on the exact M180 SHA.
10. Audit evidence and leave the PR Draft/open/unmerged.

## Required runtime configuration

For the first controlled test, the operator must deliberately provide:

- MESSENGER_AI_PROVIDER_MAP, for example {"AI-USER":"openai","AI-PEER":"anthropic"}.
- The server-side provider keys for the selected providers.
- The matching provider API-call switches, enabled only immediately before an authorized test.
- AI_PROVIDER_HOST_HMAC_KEY_HEX, exactly 32 bytes encoded as 64 hex characters.

No browser code receives provider API keys.

## Operator-only prerequisites not asserted by the local preflight

Before a real test, the operator must separately verify:

1. Each AI has an independently authenticated provider account/session appropriate to its assigned provider.
2. The Messenger server is deployed in an approved staging environment.
3. The PRIVATE room contains exactly the two selected AI identities.
4. Each AI uses its own authenticated Messenger browser session.
5. Each AI registers its own session through /v1/ai/conversation/session/register.
6. The selected provider assignments match the intended AI identities.
7. The operator has explicit authorization to enable provider API calls and accepts any provider billing/quota impact.
8. The first live exchange is a short, controlled prompt and is observed for correct sender/provider attribution.
9. Any failure immediately disables the affected provider-call switch; no automatic retry policy is implied by this mission.
10. Evidence records the deployed commit, configuration state without secret values, room ID, AI identities, provider IDs, request/correlation IDs and response status. Secret values must never be recorded.

## Preflight semantics

server.live_test_preflight.build_preflight() is intentionally offline. It reports:

- READY_FOR_OPERATOR_ACTIVATION only when all local configuration checks pass.
- BLOCKED otherwise.
- networkCallsPerformed: false.
- secretsExposed: false.

A READY result is **not** proof of provider connectivity, account validity,
quota, billing, staging deployment, room membership, session registration, or
a successful AI response.

## Fail-closed cases

The preflight blocks:

- missing or malformed provider assignment;
- duplicate JSON assignment keys;
- missing required AI assignment;
- unknown provider;
- missing selected provider credential;
- selected provider call switch disabled;
- missing or invalid 32-byte host HMAC key.

The provider router also rejects malformed/duplicate assignments and resolves an
AI only when its explicitly assigned adapter is configured and its call policy is enabled.

## Safety boundary

No test in this mission calls urllib.request.urlopen against a provider.
Provider adapter tests use mocked transport only. CI must remain provider-network
free. The PR remains Draft and unmerged.
