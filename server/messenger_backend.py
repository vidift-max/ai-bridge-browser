            raise ValueError("message_not_found")
        self.authorize_member(ai_id, message.conversation_id)
        rows = self._store.load_audio_attachments_for_message(message_id)
        if not any(row["object_id"] == object_id for row in rows):
            raise PermissionError("audio_attachment_not_authorized")
        return audio_store.read(object_id)

    @_synchronized
    def pending(self, bearer_token: str, conversation_id: str, after_sequence: int = 0, limit: int = 50) -> List[Message]:
        self._purge_expired()
        ai_id = self.authenticate(bearer_token)
        members = self._conversations.get(conversation_id)
        if not members or ai_id not in members:
            raise PermissionError("authorization_denied")
        if after_sequence < 0 or limit < 1 or limit > 100:
            raise ValueError("invalid_cursor")
        pending = [m for m in self._messages.values() if m.conversation_id == conversation_id and m.sequence > after_sequence and ai_id in m.recipient_ai_ids and ai_id not in m.acknowledged_by]
        return sorted(pending, key=lambda m: m.sequence)[:limit]

    @_synchronized
    def acknowledge(self, bearer_token: str, message_id: str) -> Message:
        self._purge_expired()
        ai_id = self.authenticate(bearer_token)
        message = self._messages.get(message_id)
        if message is None or ai_id not in message.recipient_ai_ids:
            raise PermissionError("authorization_denied")
        message.acknowledged_by.add(ai_id)
        self._store.save_ack(message_id, ai_id)
        return message