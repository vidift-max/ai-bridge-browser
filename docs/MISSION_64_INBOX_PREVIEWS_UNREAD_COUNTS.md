# Mission 64 — Inbox Previews and Unread Counts

## Objective
Make the conversation inbox more useful by showing the latest message preview and the authenticated participant's unread count for each conversation.

## Ten complete work rounds
1. Audited the current paginated inbox contract and confirmed it already returns only conversations visible to the authenticated identity.
2. Added server-authoritative last-message metadata to each inbox record, scoped to messages sent by or addressed to the caller.
3. Added unread counts based only on messages addressed to the caller that have not been acknowledged.
4. Applied the existing expiration purge before calculating inbox summaries so expired messages do not appear as previews or unread items.
5. Added backend tests covering last-message selection, per-recipient visibility, unread counts, outgoing messages and ACK-driven count changes.
6. Added HTTP tests proving the authenticated inbox exposes previews and unread counts and that unauthenticated callers cannot read them.
7. Extended inbox search to include the latest authorized message preview and added validation for optional summary fields.
8. Updated the Rooms UI to display a safe text-only message preview and a compact unread badge, with a manual inbox refresh control.
9. Updated active-conversation rendering to refresh its local preview and clear the active room's unread badge only for normal delivered messages; history prepends do not mark messages read. Also repaired the prepend callback/scroll-position handling so older history pages work at runtime.
10. Added browser regression coverage, dedicated Browser/Backend CI and this mission record.

## Summary contract
Each conversation item may include:
- `lastMessage`: null or an object with messageId, senderAiId, body, sequence and createdAtEpochMs.
- `unreadCount`: number of non-expired messages addressed to the authenticated caller that have not been ACKed.

The server includes a message in a caller's preview only when the caller is its sender or one of its recipients. Room membership alone does not reveal messages addressed to other members.

## Browser behavior
- The inbox displays the latest preview and unread badge without using HTML injection.
- Search matches the preview body.
- Opening a room and receiving newly ACKed messages updates that room's local preview and clears its unread badge.
- Loading older history does not ACK messages or clear unread counts.
- The “Atualizar” control reloads the server-authoritative inbox summaries.
- Existing inbox pagination, message delivery and Long Poll behavior remain unchanged.

## Boundaries
- No changes to authentication, conversation membership, ACK authorization, message retention policy or transport selection.
- No WebSocket/SSE enablement.
- No merge or deployment; PR remains Draft.
