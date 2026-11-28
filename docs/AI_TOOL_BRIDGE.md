# AI Tool Bridge — Contract v1.1 (clean-room adapters)

## Status
Five independent local-only adapters are implemented and marked READY in the catalog. They are **not automatically granted to any AI principal**. Discovery and invocation require a separate durable `TOOL_USE` grant for the authenticated AI identity. No grants are provisioned by default.

The archived `AI_Tool_Hub_Pacote_Independente.zip` remains preserved as historical evidence only. Its SHA-256 is `f5415aabd795da2f30fcbbaca1cfb40cfb0f68a8235e5e4f36d2806f09253cee`. Its license and authorship remain unclear. The new adapters in `server/tool_adapters.py` were authored independently for this repository and do not import, copy, adapt, bundle, or execute files from that ZIP. The old package is not a runtime dependency.

## Tools and limits

| Tool | Capability | Runtime limits |
|---|---|---|
| `duration_timer` | Parse/format durations or return seconds | 64-character input; maximum 7 days; linear token parser |
| `recipe_scaler` | Scale ingredient quantities | 1–100 ingredients; 100-character names; finite amounts ≤ 1,000,000; servings ≤ 10,000; units preserved (no guessed conversions) |
| `quiz_engine` | Build quiz payload or score answers | 1–100 questions; 2–10 options/question; bounded text; no HTML rendering |
| `svg_chart` | Produce bar/line SVG | 1–50 labels; 1–6 series; 200–2000 × 150–2000; values 0–1,000,000; XML text escaped; output ≤ 32 KiB |
| `link_card` | Validate and normalize link metadata | URL ≤ 2048; HTTP(S) only; no credentials; local/private/reserved IPs and legacy IPv4 spellings rejected; **no title fetch or network request** |

The implementation is local and synchronous. It does not access network, filesystem, shell, browser DOM, external processes, or credentials. The link-card adapter returns structured metadata, not executable HTML. The SVG renderer emits a fixed element/attribute set and escapes all user-provided text.

## API

- `GET /v1/tools/capabilities`: authenticated AI identity derived from bearer principal; only explicitly granted READY tools are returned, including their versioned input/output JSON Schemas.
- `POST /v1/tools/{toolId}/invoke`: authenticated, authorized invocation. JSON body:
  `{"requestId":"<UUID>","toolVersion":"1.0.0","input":{...}}`.
- `POST /v1/admin/tool-permissions`: administrator-only grant; body `{"principalAiId":"AI-01","toolId":"duration_timer"}`.
- `DELETE /v1/admin/tool-permissions/{principalAiId}/{toolId}`: administrator-only revocation.
- `GET /v1/admin/tool-permissions` and `/audit`: administrator-only grant/audit inspection.

The HTTP layer never trusts caller-supplied AI identity. It obtains the principal from the authenticated bearer token. Messenger room membership does not grant `TOOL_USE`. Grants are durable in SQLite and audit events are append-only. The administrator bearer is separate from AI credentials and configured via `TOOL_HUB_ADMIN_TOKEN`; it must not be committed or shared with agents.

## Validation and error behavior

- Request body maximum: 10,000 bytes, checked before JSON parsing.
- Sliding-window limit: 60 requests/minute per authenticated principal and tool (in-memory limiter; resets on process restart).
- Tool version must exactly match the catalog version.
- Unknown fields and invalid values are rejected by strict adapter input validators.
- Result JSON is finite and bounded to 32 KiB.
- Errors use stable codes such as `INVALID_REQUEST`, `INVALID_FORMAT`, `OUT_OF_RANGE`, `UNKNOWN_UNIT`, `INVALID_QUIZ`, `INVALID_ANSWERS`, `INVALID_SPEC`, `INVALID_SIZE`, `INVALID_URL`, and `OUTPUT_TOO_LARGE`.
- No request payload, token, password, or credential is written to audit metadata.

## AI-01 / AI-02 provisioning plan

After deployment and confirmation that the configured bearer principals really map to logical AI-01 and AI-02, an owner-controlled administrator must create these exact grants:

| Principal | Tool IDs |
|---|---|
| AI-01 | duration_timer, recipe_scaler, quiz_engine, svg_chart, link_card |
| AI-02 | duration_timer, recipe_scaler, quiz_engine, svg_chart, link_card |

This is ten independent grants via `POST /v1/admin/tool-permissions`, each with `{"principalAiId":"AI-01","toolId":"duration_timer"}` (substitute the row's principal and tool). Verify with `GET /v1/admin/tool-permissions`, then test `GET /v1/tools/capabilities` using each agent's own bearer credential. Never give the administrator token to an agent. Do not provision until `MESSENGER_AI_ID_A` and `MESSENGER_AI_ID_B` have been checked against the intended AI-01/AI-02 mapping; the server accepts configured IDs such as AI-GPT6 or AI-CLAUDE, so labels must not be assumed.

## Remaining integration boundaries

- Tool adapters and API are implemented in this branch, but CI must pass before claiming verified readiness.
- No default grants have been created for AI-01 or AI-02. Each of the ten grants (five tools × two agents) must be provisioned through the administrator API in the deployed database.
- Android UI/capability display and the actual AI agent runtime's discovery/invocation client are not wired by this change.
- The API is not deployed and no live AI client/device invocation is claimed.
- No merge or deployment is included.
