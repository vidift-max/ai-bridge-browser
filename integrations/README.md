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
executed. Tool-specific input/output schemas, reviewed adapters/executors, durable
permission grants, administrator grant/revoke flow, production per-tool rate
limits, sandboxing, and Android UI wiring are not implemented.

The server now has authenticated HTTP capability discovery and an invocation
route that is deliberately deny-only. Discovery filters by the authenticated
AI principal's explicit in-memory `TOOL_USE` grants and READY catalog state;
currently it returns no tools. Invocation returns 403 without a grant, 409
for any currently blocked tool, and would return 501 for a hypothetical READY
tool because no executor exists. No request can execute Tool Hub code.
Messenger access and room membership never grant tool access.

No tool can be invoked in this state.
