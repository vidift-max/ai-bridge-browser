# AI Bridge — Authorization Model

Authorization is separate from identity, room membership, and tool capability discovery.

## Levels
- CONNECT: may establish an AI Bridge session.
- JOIN_ROOM: may participate in a specific room.
- SEND_MESSAGE: may publish chat messages.
- RECEIVE_MESSAGE: may receive addressed room messages.
- TOOL_USE: separate permission for a specific tool ID.
- GITHUB_WRITE: separate permission and never implied by chat access.

## Tool-use rules
- Grants are bound to the authenticated AI principal and exact tool IDs.
- Missing grants deny by default.
- Unknown tool IDs and unknown permission names are rejected.
- Capability discovery does not grant permission.
- A disabled/blocked catalog entry cannot be invoked even when a principal has a grant.
- Tool grants are stored in the Messenger SQLite database (schema v3) and survive store/process recreation.
- Grant/revoke events are append-only in `tool_permission_audit`.
- Grant administration uses a separate `TOOL_HUB_ADMIN_TOKEN` bearer, minimum 32 characters, fail-closed when absent.
- The AI identity is derived from the bearer principal; request-body AI IDs are never authoritative.
- AI-01 and AI-02 must each receive explicit grants for each tool they are allowed to use. No default grant is provisioned.
- Messenger room membership, invitation acceptance, or message permissions do not imply `TOOL_USE`.

## Current clean-room Tool Hub
The five independent local-only adapters are `duration_timer`, `recipe_scaler`, `quiz_engine`, `svg_chart`, and `link_card`. They are cataloged READY only in the clean-room adapter branch. The archived third-party/unclear-license ZIP is not imported or executed.

## Operational boundaries
No external AI receives GitHub write access in this stage. Tokens are never stored in room messages, tool payloads, capability responses, or audit metadata. No agent should receive the administrator bearer token; only the owner-controlled admin operation may provision grants.
