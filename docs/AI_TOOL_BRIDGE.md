# AI Tool Bridge — Contract v1 (pre-integration)

## Status

This document defines the neutral boundary for a future AI Tool Hub adapter.
It does **not** mean that any tool is installed, executable, authenticated for
tool use, or available to an AI account.

The five catalog entries are deliberately disabled with
`BLOCKED_LICENSE_REVIEW`. The original package's license and rights holder
have not been established. No source code from that package may be copied,
adapted, bundled, or executed by this bridge until that review is resolved
and the user authorizes use.

## Supported catalog identifiers

- `duration_timer`
- `recipe_scaler`
- `quiz_engine`
- `svg_chart`
- `link_card`

These identifiers are stable names only. They are not proof that an adapter
or a tool-specific input/output schema exists.

## Contract files

- `registry/tool-hub/catalog.json`: current five-tool catalog and explicit
  disabled state.
- `registry/tool-hub/catalog.schema.json`: catalog shape.
- `registry/tool-hub/tool-invocation.schema.json`: generic invocation
  envelope; it is not a substitute for a tool-specific input schema.
- `registry/tool-hub/tool-result.schema.json`: stable result/error envelope.
- `server/tool_permissions.py`: deny-by-default, per-principal `TOOL_USE` grants with durable SQLite-backed grant/revoke/list operations.
- `server/tool_admin_auth.py`: separate administrator bearer authentication; requires `TOOL_HUB_ADMIN_TOKEN` with at least 32 characters.
- `server/tool_hub.py`: strict catalog loader, authenticated-principal discovery filtering, and fail-closed invocation gate; it deliberately has no executor.
- `server/test_tool_hub.py`, `server/test_tool_hub_http.py`, `server/test_tool_permission_store.py`, and `server/test_tool_admin_auth.py`: service, HTTP, persistence, and administrator-auth regression tests.

## Required request identity and authorization

1. Authenticate the bearer credential at the server boundary.
2. Derive the caller AI identity from the authenticated principal. Never trust
   a caller-supplied `aiId`, `senderAiId`, or role in the request body.
3. Require a separate explicit `TOOL_USE` grant for that exact principal.
   Messenger membership, `CONNECT`, `JOIN_ROOM`, and `SEND_MESSAGE` do not
   imply `TOOL_USE`.
4. Require that the requested tool is present in the catalog and has
   `enabled: true` and status `READY`.
5. Validate the complete request against the generic envelope and the
   selected tool's versioned input schema before execution.
6. Recheck authorization and enabled status at invocation time; discovery
   visibility is not an authorization token.

AI tool grants and append-only grant/revoke audit events are stored in the Messenger SQLite database (schema v3) and survive process/store recreation. Grants remain deny-by-default. Grant management uses a separate administrator bearer token configured through `TOOL_HUB_ADMIN_TOKEN` (minimum 32 characters); it is never the AI bearer token. If the variable is absent or weak, administrative routes fail closed with 503. The HTTP layer derives the AI identity from the authenticated AI bearer principal; request-body identity claims are not accepted for Tool Hub authorization.

## HTTP surface (implemented deny-only boundary)

- `GET /v1/tools/capabilities`: implemented; authenticates the bearer token,
  derives the principal server-side, and returns only tools with an explicit
  `TOOL_USE` grant and `enabled: true` plus status `READY`. Current response
  is empty because all five catalog records are blocked and no grants are
  provisioned by default.
- `GET /v1/admin/tool-permissions`: administrator-only listing of durable grants.
- `GET /v1/admin/tool-permissions/audit`: administrator-only read of durable grant/revoke audit history.
- `POST /v1/admin/tool-permissions`: administrator-only grant creation/update using a principal AI ID and tool ID.
- `DELETE /v1/admin/tool-permissions/{principalAiId}/{toolId}`: administrator-only revocation.
  Admin routes use a separate `TOOL_HUB_ADMIN_TOKEN`, constant-time bearer comparison, rate limiting, and audit events. No default admin token is created or committed.
- `POST /v1/tools/{toolId}/invoke`: route and authorization gate implemented.
  Missing grants return 403; unknown IDs return 404; blocked/disabled tools
  return 409. If a tool were marked READY, the current service still returns
  501 because no executor/adapter exists. The endpoint does not parse or run
  a tool payload and cannot execute any tool.

AI discovery/invocation and admin routes use the existing in-memory sliding-window limiter (60 requests/minute by default). Permission data is durable, but the limiter is not. This is not per-tool production quotas, a deployed endpoint, or proof of live AI clients.

## Bounds and execution requirements

- Request body maximum: 32 KiB, enforced before JSON parsing.
- Invocation deadline: 1–30,000 ms; server-side deadline is authoritative.
- Tool-specific limits must be explicit in each tool schema and adapter.
- Rate limiting must be per authenticated principal and per tool; a client
  cannot select or reset its own quota.
- Reject unknown fields, invalid types, oversized arrays/strings, and
  unsupported versions. Do not silently coerce or discard malformed values.
- No network access, filesystem access, shell execution, or DOM automation
  unless a separately reviewed capability explicitly grants it.
- Treat tool output as untrusted data. Render text with safe text APIs; never
  inject tool output as HTML. SVG output requires XML parsing, element and
  attribute allowlists, size limits, and rejection of active/external content.
- Never include bearer tokens, session tokens, passwords, or raw credentials
  in logs, errors, correlation metadata, or tool inputs.

## Result and error contract

A result carries `requestId`, `toolId`, and one status:
`SUCCEEDED`, `REJECTED`, `FAILED`, or `TIMED_OUT`. Failure responses use
stable machine-readable error codes from
`tool-result.schema.json`; internal exception messages and stack traces are
not returned to callers.

## Current implementation boundary

Implemented in this branch:
- catalog and generic JSON Schema files;
- explicit disabled records for the five tool IDs;
- durable SQLite-backed `TOOL_USE` grants with administrator grant/list/revoke routes;
- separate fail-closed administrator bearer authentication and append-only durable grant/revoke audit history;
- schema v2/v3 migrations with read-only recovery compatibility;
- authenticated capability discovery and deny-only invocation;
- regression tests for authorization, admin auth, persistence, and HTTP routes;
- this contract document.

Not implemented:
- source-license approval or source provenance decision;
- tool-specific schemas and adapters/executors;
- production-grade admin identity provider/rotation workflow and per-tool quotas;
- sandboxing, output sanitization, and Android UI wiring.

Until license approval, tool-specific schemas, reviewed adapters, and explicit
grants are implemented, the five tools remain unavailable. No invocation can
reach executable code in the current implementation.
