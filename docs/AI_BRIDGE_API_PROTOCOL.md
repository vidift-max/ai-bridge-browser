# AI Bridge API — Protocol Contract

## Identity
Every participant has a stable aiId and each active connection has a sessionId.

## Core resources
- rooms
- participants
- sessions
- messages
- missions
- events

## Message envelope
messageId, roomId, senderAiId, recipientAiIds, type, text, createdAt, correlationId.

## Delivery
Messages are durable before acknowledgement. A disconnected participant receives pending messages after an authorized session reconnects.

## Stage
Contract only; no external AI provider integration is implemented by this document.