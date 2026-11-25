# Mission 178 — Independent Agent Providers and First Live Test Readiness

## Objective
Give each Messenger AI identity an explicit server-side provider assignment, implement independent official API adapters for OpenAI, Anthropic Claude and Google Gemini, and expose a safe readiness preflight. This mission does not deploy, log in to provider accounts, or make live API calls.

## Ten engineering rounds
1. Audit Mission 177 PR #179, source SHA, provider host, session bridge and workflow evidence.
2. Trace provider bootstrap, credential sources, API policy gates and existing provider catalog.
3. Define explicit per-agent provider assignment via server-only MESSENGER_AI_PROVIDER_MAP JSON.
4. Implement a router that resolves an adapter only for an explicitly assigned identity.
5. Add Anthropic Messages API adapter with its own server-side key and fail-closed call switch.
6. Add Gemini generateContent adapter with its own server-side key and fail-closed call switch.
7. Keep OpenAI, Anthropic and Gemini credentials server-side; no browser token or secret exposure.
8. Wire the provider router into the two-agent host and add authenticated readiness endpoint.
9. Add deterministic fake-adapter, policy-gate, invalid-assignment and provider-catalog tests.
10. Run exact-SHA CI, inspect jobs, and leave a Draft PR unmerged.

## Configuration contract
- `MESSENGER_AI_PROVIDER_MAP`: JSON object mapping exact AI IDs to `openai`, `anthropic`, or `google_gemini`. Example shape: `{"AI-A":"openai","AI-B":"anthropic"}`. No assignment is inferred.
- OpenAI: `OPENAI_API_KEY` and `OPENAI_API_CALLS_ENABLED=true`.
- Anthropic: `ANTHROPIC_API_KEY` and `ANTHROPIC_API_CALLS_ENABLED=true`.
- Gemini: `GEMINI_API_KEY` and `GEMINI_API_CALLS_ENABLED=true`.
- Claude and Gemini use independent server-side credentials and independent switches. A key alone does not enable a paid request.
- `POST /v1/ai/conversation/session/register` still requires each AI to register its own Messenger session.
- Authenticated `GET /v1/ai/provider/readiness` reports provider assignment, implementation, configuration and policy state without returning credentials.
- The host HMAC key and existing two-agent room/session prerequisites from Mission 177 remain required.

## Evidence and limitations
- CI uses fake adapters; it must not contact provider APIs.
- `READY` means adapter assigned, credential present and explicit policy switch enabled. It does not prove network reachability, provider account validity, quota, billing, or a successful live response.
- No live API call, secret provisioning, deployment, real login, device activation or two-AI conversation is performed by this mission.
- Existing in-memory Messenger session limitations remain unchanged.
- Provider API schemas and model names are adapter defaults; model names may be overridden server-side. Real integration still requires staging validation and explicit authorization.
