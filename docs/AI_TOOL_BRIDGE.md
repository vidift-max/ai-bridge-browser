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
- `server/tool_permissions.py`: deny-by-default, per-principal
  `TOOL_USE` authorization primitive.

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

The current permission registry is an in-memory primitive only. It is not
wired to an HTTP route, durable grant store, or administrator workflow. No
principal currently receives an implicit grant.

## Proposed HTTP surface (not implemented)

- `GET /v1/tools/capabilities`: authenticated discovery, filtered by the
  caller's `TOOL_USE` grant and enabled catalog state.
- `POST /v1/tools/{toolId}/invoke`: authenticated invocation after all
  authorization and schema checks.

These routes are contract targets only. They must not be described as live
until implemented and covered by HTTP integration tests.

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
- a deny-by-default in-memory `TOOL_USE` permission primitive and unit tests;
- this contract document.

Not implemented:
- source-license approval or source provenance decision;
- tool-specific schemas and adapters;
- HTTP capability-discovery or invocation routes;
- durable permission grants, administrator grant/revoke flow, or per-tool
  production rate limits;
- sandboxing, output sanitization, integration tests, or Android UI wiring.

Until those items are addressed, the five tools remain unavailable and all
invocation attempts must be rejected.
