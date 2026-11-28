# AI Bridge — Authorization Model

Authorization is separate from identity and room membership.

## Levels

- CONNECT: may establish an AI Bridge session.
- JOIN_ROOM: may participate in a specific room.
- SEND_MESSAGE: may publish chat messages.
- RECEIVE_MESSAGE: may receive addressed room messages.
- TOOL_USE: separate permission for a specific tool or explicitly approved
  tool set. It is never implied by any other permission.
- GITHUB_WRITE: separate permission and never implied by chat access.

## Tool-use rules

- Grants are bound to the authenticated AI principal and exact tool IDs.
- Missing grants deny by default.
- Unknown tool IDs and unknown permission names are rejected.
- A capability-discovery response does not grant permission.
- A catalog entry marked disabled or blocked cannot be invoked even when a
  principal has a grant.
- Grant, revocation, expiry, and administrative attribution must be audited
  before a durable or production grant workflow is enabled.
- The current `server/tool_permissions.py` registry is an in-memory policy
  primitive only; it is not connected to authentication, HTTP routes, durable
  storage, or an admin console.

No external AI receives GitHub write access in the current stage.

Credentials and tokens are never stored in room messages, tool payloads,
capability responses, or audit metadata.
