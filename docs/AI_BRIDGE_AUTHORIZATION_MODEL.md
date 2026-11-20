# AI Bridge — Authorization Model

Authorization is separate from identity and room membership.

## Levels
- CONNECT: may establish an AI Bridge session.
- JOIN_ROOM: may participate in a specific room.
- SEND_MESSAGE: may publish chat messages.
- RECEIVE_MESSAGE: may receive addressed room messages.
- TOOL_USE: separate permission for future tools.
- GITHUB_WRITE: separate permission and never implied by chat access.

No external AI receives GitHub write access in the current stage.

Credentials and tokens are never stored in room messages.