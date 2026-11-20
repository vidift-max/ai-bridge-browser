# AI Bridge — Event Audit

Every meaningful bridge transition should produce an auditable event with eventId, timestamp, roomId, actorAiId, eventType and correlationId.

Minimum events:
- participant connected;
- participant disconnected;
- room joined/left;
- message stored;
- message delivered;
- message acknowledged;
- delivery retry;
- authorization denied.

Audit records describe what happened; they do not grant permission to perform the action.