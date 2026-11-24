# Mission 40 — Room-Scoped Acknowledgement Authorization

## Goal
Ensure a message ACK is accepted only from an authenticated recipient who is still a member of the exact conversation containing that message.

## Implementation
- Resolve the message before authorization and derive its authoritative conversation ID from stored state.
- Require current membership in that conversation and membership in the message's recipient list.
- Preserve idempotent ACK behavior while avoiding redundant persistence writes.
- Keep the existing HTTP Long Poll and message ACK endpoint shape unchanged.

## Validation cases
- Current authorized recipient can ACK.
- Sender and non-recipient cannot ACK.
- Former room member cannot ACK after membership removal.
- Membership in a different room does not grant ACK authority.
- Repeated authorized ACK is idempotent.
- Existing restart test continues to verify ACK persistence.

## Scope boundaries
No WebSocket/SSE, provider identity verification or automation, deployment, or physical-device validation is claimed.
