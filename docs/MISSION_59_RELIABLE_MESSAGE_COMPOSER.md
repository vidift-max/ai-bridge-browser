# Mission 59 — Reliable Message Composer and Idempotent Retry

## Objective
Make the existing room composer safe to retry when a message POST may have reached the server but its response was lost.

## Ten completed work rounds
1. Audited the UI adapter and server `submit` contract; confirmed the server deduplicates by authenticated sender plus `clientRequestId` and rejects conflicting payload reuse.
2. Added a pending composer-attempt record scoped to conversation and exact body.
3. Generate one message ID and one client request ID for each logical send attempt.
4. Pass both stable identifiers through the existing room UI messenger adapter.
5. Preserve the pending attempt after network, authorization, or server errors so a retry can reuse the same idempotency keys.
6. Clear the pending attempt only after the server confirms success.
7. Keep the draft text intact after an unconfirmed send; clear it only when the same text is successfully accepted in the same conversation.
8. Block overlapping form submissions and expose a clear sending state.
9. Added regression tests proving identical IDs and payload on retry, fresh attempt creation for changed drafts, and duplicate-submit protection.
10. Added mission documentation and a dedicated Browser/Backend/Android regression workflow; PR remains Draft.

## Safety boundaries
- The server remains authoritative for authentication, room membership, recipient authorization, persistence, and idempotency.
- A retry is safe only when the user resubmits the same text in the same conversation; edited text intentionally becomes a new logical message.
- No optimistic success is displayed before the server responds.
- No message delivery to an external AI, physical device, or phone is claimed.
- HTTP Long Poll remains the only enabled realtime transport.
- No merge or deployment is performed.
