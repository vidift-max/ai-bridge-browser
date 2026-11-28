# External AI and Tool Hub Integrations

## Provider integrations

Planned provider adapters:
- Kimi
- Gemini
- Generic authorized AI provider

Claude is paused and receives no new integration work or tasks.

Provider credentials and private account data must never be committed.

## Local AI Tool Hub

The current Tool Hub integration scope is limited to these five tools:

- `duration_timer`
- `recipe_scaler`
- `quiz_engine`
- `svg_chart`
- `link_card`

The neutral catalog and generic request/result contracts are under
`registry/tool-hub/`; the contract is documented in
`docs/AI_TOOL_BRIDGE.md`.

**Current status: BLOCKED — NOT INTEGRATED.**

All five catalog entries are disabled. The original package's license and
rights holder are not established. Until the user confirms the license/usage
rights, no original package source may be copied, adapted, bundled, or
executed. Tool-specific input/output schemas, adapters, HTTP discovery and
invocation routes, durable permission grants, and integration tests are not
implemented.

The server contains only a deny-by-default, in-memory `TOOL_USE` policy
primitive with unit tests. It is not yet wired to authenticated HTTP requests.
Messenger access and room membership never grant tool access.

No tool can be invoked in this state.
