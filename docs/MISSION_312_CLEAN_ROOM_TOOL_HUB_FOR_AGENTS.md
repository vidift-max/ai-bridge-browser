# M312 — Clean-room AI Tool Hub for AI-01 / AI-02

Date: 2026-11-28  
Branch: `feat/tool-hub-cleanroom-agent-adapters`  
Stacked on: `fix/browser-session-isolation-https-policy`  
Draft PR: #246  
Final HEAD: `8f798e423a71b02785931f6b00512bc8e491234b`.

## Ten rounds

1. **PASS — source evidence:** located the archived Tool Hub ZIP and read the preserved audit. SHA-256: `f5415aabd795da2f30fcbbaca1cfb40cfb0f68a8235e5e4f36d2806f09253cee`; 94,977 bytes; 56 entries.
2. **PASS — rights boundary:** confirmed no LICENSE/copyright/rights-holder authorization in the historical evidence. Original source remains untouched and is not imported, copied, adapted, bundled or executed.
3. **PASS — independent adapters:** authored local-only implementations for duration_timer, recipe_scaler, quiz_engine, svg_chart and link_card in `server/tool_adapters.py`.
4. **PASS — schemas:** added ten versioned per-tool input/output JSON Schema files and aligned the generic invocation envelope.
5. **PASS — catalog:** published all five clean-room adapters as READY version 1.0.0; ToolHubService verifies each schema reference resolves inside the registry and includes the schemas in authorized capability discovery.
6. **PASS — invocation:** connected the authenticated HTTP route to the adapters; server derives AI identity from bearer principal, not request body.
7. **PASS — guardrails:** strict request envelope/version, duplicate-key rejection, 10,000-byte request limit, 32 KiB adapter result limit, per-principal/per-tool 60-per-minute sliding window; no network/filesystem/shell/DOM access.
8. **PASS — security behavior:** link_card rejects credentials, unsafe schemes and local/private/reserved IP destinations and performs no fetch; svg_chart escapes user text and emits a fixed SVG shape; quiz/link card return data, not HTML.
9. **PASS — Android client boundary:** `MessengerHttpClient` now provides authenticated capability discovery and tool invocation using its own bearer credential. The request body has a generated UUID and does not contain an AI identity. Unit tests cover the invocation envelope and local allowlist.
10. **PASS — CI:** backend workflow #874 — SUCCESS, **249 tests passed**, exact tested HEAD `8f798e423a71b02785931f6b00512bc8e491234b`; Android Build workflow #1576 — SUCCESS, debug APK build and Android unit tests passed on the same HEAD.

## Current state

- Catalog: five tools READY in this branch.
- Invocation: backend API and Android HTTPS client methods implemented.
- Capability discovery returns each granted tool's versioned input/output schemas.
- Grants: still deny-by-default; no AI-01/AI-02 grants have been created.
- Identity mapping: runtime configuration maps bearer tokens through `MESSENGER_AI_ID_A` and `MESSENGER_AI_ID_B`; actual mapping to logical AI-01 and AI-02 must be verified before provisioning.
- Agent runtime: the client methods are available, but the autonomous agent decision/orchestration loop has not yet been connected to call them.
- Original ZIP: historical evidence only; license remains unresolved, but new implementations are independently authored.
- PR #246 remains Draft / OPEN / not merged. No deployment or release.

## Remaining work before agents can actually use the tools

1. Verify the deployed server principal IDs correspond to AI-01 and AI-02.
2. Provision ten explicit grants (five tools × two principals) with owner-held admin bearer; never disclose the admin bearer to agents.
3. Connect the agent orchestration loop to capability discovery and invocation, using each agent's own bearer credential.
4. Run authenticated end-to-end tests for both agents, including cross-agent denial and grant revocation.

## CI evidence
- Backend: run `46126460132`, job `140922026053`, SUCCESS; `Ran 249 tests`.
- Android: run `46126460153`, job `140922026229`, SUCCESS; `gradle :app:assembleDebug` and `gradle :app:testDebugUnitTest` both completed successfully.
- Earlier pre-fix run #855 failed due to an over-escaped SemVer regex and legacy tests asserting the blocked-only contract. Both causes were corrected before the successful runs above.
