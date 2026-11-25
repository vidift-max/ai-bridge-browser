# M140 — Rooms Conversation Runtime Integration

## Objective
Expose the bounded two-agent conversation runtime in the Rooms interface while keeping it disabled unless an authenticated provider host is present.

## Ten rounds
1. Audited M139 and confirmed the runtime was not mounted by Rooms.
2. Added a dedicated conversation panel with a first-message field, bounded turn choices and explicit start/stop controls.
3. Restricted panel availability to an authenticated identity in an exact two-member PRIVATE room.
4. Added a fail-closed host contract: `window.AIBridgeAgentHost.requestAgent` and `verifyAttestation` must both exist.
5. Connected the panel to the M139 runtime and M138 bounded controller.
6. Routed verified results to the existing Rooms message renderer without forging sender identity or writing directly as the peer.
7. Served the four runtime assets through an explicit HTTP allowlist with no-store and nosniff headers.
8. Added UI, membership, host-gating and asset-route contract tests.
9. Added a dedicated CI workflow for Node runtime tests and Python HTTP route tests.
10. Documented remaining production requirements and opened a draft PR without merge or deployment.

## User experience
- The panel appears when a room is opened.
- It is enabled only for exactly two members in a PRIVATE room and only when a trusted host exposes both provider request and attestation verification functions.
- Without that host, the button remains disabled and the UI explicitly says no AI was contacted.
- The user chooses the first message and a maximum of 2–20 turns (default 6), then explicitly starts or stops the run.

## Security boundary
The host must authenticate each agent independently, keep provider credentials server-side, and verify a cryptographic attestation binding conversation ID, agent ID, response body and turn. The panel does not implement or simulate that host. The current repository does not yet ship a production `AIBridgeAgentHost`; therefore this PR does not establish live AI-to-AI communication.

## Validation
CI is defined to run:
- `node --test web/ai-conversation-panel.test.mjs web/ai-agent-adapter.test.mjs web/ai-conversation-runtime.test.mjs web/ai-conversation-loop.test.mjs`
- `python -m unittest server.test_http_server`

Authored tests are not a passing result. Check the GitHub Actions run on the final head SHA before claiming PASS.

## Explicit non-goals
No private ChatGPT tab access, cookie/session scraping, fake provider host, paid API, secrets, Render resources, deployment, physical device activation, merge or automatic start.
