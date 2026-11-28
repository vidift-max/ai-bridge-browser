# M312 — Clean-room AI Tool Hub for AI-01 / AI-02

Date: 2026-11-28  
Branch: `feat/tool-hub-cleanroom-agent-adapters`  
Stacked on: `fix/browser-session-isolation-https-policy`  
Draft PR: #246.

## Ten rounds

1. **PASS — source evidence:** located the archived Tool Hub ZIP and read the preserved audit. SHA-256: `f5415aabd795da2f30fcbbaca1cfb40cfb0f68a8235e5e4f36d2806f09253cee`; 94,977 bytes; 56 entries.
2. **PASS — rights boundary:** confirmed no LICENSE/copyright/rights-holder authorization in the historical evidence. Original source remains untouched and is not imported, copied, adapted, bundled or executed.
3. **PASS — independent adapters:** authored local-only implementations for duration_timer, recipe_scaler, quiz_engine, svg_chart and link_card in `server/tool_adapters.py`.
4. **PASS — schemas:** added ten versioned per-tool input/output JSON Schema files and aligned the generic invocation envelope.
5. **PASS — catalog:** published all five clean-room adapters as READY version 1.0.0; ToolHubService verifies each schema path resolves inside the registry.
6. **PASS — invocation:** connected the authenticated HTTP route to the adapters; server derives AI identity from bearer principal, not request body.
7. **PASS — guardrails:** strict request envelope/version, duplicate-key rejection, 10,000-byte request limit, 32 KiB adapter result limit, per-principal/per-tool 60-per-minute sliding window; no network/filesystem/shell/DOM access.
8. **PASS — security behavior:** link_card rejects credentials, unsafe schemes and local/private IP destinations and performs no fetch; svg_chart escapes user text and emits a fixed SVG shape; quiz/link card return data, not HTML.
9. **PASS — tests authored and first CI diagnostics resolved in source:** added adapter/service/HTTP/catalog tests. First observed CI run #855 failed with 249 tests (1 failure, 33 errors) because the SemVer regex was over-escaped and catalog/HTTP tests still asserted the old blocked-only contract. Fixed the regex and updated tests to the new request envelope and READY catalog.
10. **BLOCKED — final CI and agent provisioning:** no workflow result has yet been returned for the post-fix HEAD. No deployment, admin grant, Android client wiring, or real-agent invocation was performed.

## Current state

- Catalog: five tools READY in this branch.
- Invocation: implemented in backend and requires per-tool `TOOL_USE`.
- Grants: still deny-by-default; no AI-01/AI-02 grants have been created.
- Identity mapping: runtime configuration maps bearer tokens through `MESSENGER_AI_ID_A` and `MESSENGER_AI_ID_B`; actual mapping to logical AI-01 and AI-02 must be verified before provisioning.
- Android/agent runtime: no Tool Hub discovery/invocation client is wired into the AI agent loop yet.
- Original ZIP: historical evidence only; license remains unresolved, but new implementations are independently authored.
- PR #246 remains Draft / OPEN / not merged. No deploy or release.

## Next required steps

1. Obtain green backend CI on exact final HEAD.
2. Verify the deployed server principal IDs correspond to AI-01 and AI-02.
3. Provision ten explicit grants (five tools × two principals) with owner-held admin bearer; never disclose the admin bearer to agents.
4. Wire Android/agent orchestration to capability discovery and invocation using each agent's own bearer credential.
5. Run authenticated end-to-end tests per agent and verify isolation/revocation.
