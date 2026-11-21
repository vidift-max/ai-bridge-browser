# AI MESSENGER — Round 06/10 — Local Inbox/Outbox Structure

Status: IMPLEMENTED LOCALLY / REMOTE TRANSPORT NOT IMPLEMENTED
Mission: 03 — AI MESSENGER
Repository: `vidift-max/ai-bridge-browser`
Branch: `v2-saas-alpha`

## Objective

Create a truthful local structure for the future Messenger inbox/outbox without claiming that any message has crossed the internet or reached another AI.

## Implemented

- `MessengerTransportRecord` provides a local transport record linked to a message and conversation.
- Two explicit directions exist:
  - `LOCAL_OUTBOX`: local record representing a message prepared/saved on this device.
  - `LOCAL_INBOX`: local record shape reserved for a future authenticated incoming message.
- Every record remains `LOCAL_ONLY`.
- Each record has its own local record ID and references the message ID.
- The model validates conversation, message, direction, participant and timestamp fields.
- Unit tests cover valid outbox/inbox records and invalid input.

## Messenger UI behavior

The existing Messenger now records a local outbox entry when the user saves a local message. The UI can summarize local inbox/outbox counts while continuing to identify the entire flow as local-only.

No remote send button, provider API, authenticated session, delivery receipt or external AI communication is created by this round.

## Explicit non-claims

This round does **not** implement:

- server inbox/outbox;
- HTTP/WebSocket transport;
- authenticated AI_ID;
- remote participant delivery;
- SENT, DELIVERED or ACKNOWLEDGED state;
- offline server queue;
- provider adapter;
- physical-device communication test.

Those remain future work governed by `docs/AI_MESSENGER_PROTOCOL.md`.

## Acceptance evidence

- `MessengerTransportRecordTest` validates the local record contract.
- Android build/test CI must pass on the final commit before this round is marked complete.
