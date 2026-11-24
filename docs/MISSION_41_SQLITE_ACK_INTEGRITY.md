# Mission 41 — SQLite ACK Persistence Integrity

## Objective
Make the durable storage layer independently enforce the invariants required for a message acknowledgement.

## Changes
- ACK persistence now requires a non-empty string message ID and AI ID.
- The referenced message must exist.
- The AI must be in that message's persisted recipient list.
- The AI must still belong to the message's persisted conversation.
- The insert runs inside a SQLite IMMEDIATE transaction and rolls back on validation or storage errors.
- The method reports whether a new ACK row was inserted; repeated ACKs remain idempotent.
- Existing message deletion cleanup remains covered for acknowledgement rows.

## Regression coverage
- Unknown message, non-recipient, and former room member rejection.
- Blank and non-string identifier rejection.
- First insert vs duplicate insert return values.
- ACK durability through store restart.
- ACK cleanup when the message is deleted.
- Backend state remains pending when ACK persistence raises, allowing a safe retry.

## Scope
The transport remains HTTP Long Poll. This mission does not add WebSocket/SSE, provider automation, deployment, or physical-device validation.
