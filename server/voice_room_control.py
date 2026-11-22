"""Authorization policy for administrative voice controls in Messenger rooms.

This is a server-side policy model only. It does not capture, transmit, or mute audio.
The caller must supply trusted admin AI IDs from deployment configuration.
"""
from threading import RLock


class VoiceRoomControl:
    def __init__(self, admin_ai_ids):
        if not isinstance(admin_ai_ids, (set, frozenset, list, tuple)):
            raise ValueError("invalid_voice_admin_ids")
        normalized = {item.strip() for item in admin_ai_ids
                      if isinstance(item, str) and item.strip()}
        if len(normalized) != len(admin_ai_ids):
            raise ValueError("invalid_voice_admin_ids")
        self._admin_ai_ids = frozenset(normalized)
        self._muted = set()
        self._lock = RLock()

    def mute(self, acting_ai_id, conversation_id, target_ai_id, conversations):
        return self._set_muted(True, acting_ai_id, conversation_id,
                               target_ai_id, conversations)

    def unmute(self, acting_ai_id, conversation_id, target_ai_id, conversations):
        return self._set_muted(False, acting_ai_id, conversation_id,
                               target_ai_id, conversations)

    def is_muted(self, conversation_id, ai_id):
        with self._lock:
            return (conversation_id, ai_id) in self._muted

    def muted_participants(self, conversation_id):
        with self._lock:
            return frozenset(ai_id for room_id, ai_id in self._muted
                             if room_id == conversation_id)

    def _set_muted(self, muted, acting_ai_id, conversation_id,
                   target_ai_id, conversations):
        if acting_ai_id not in self._admin_ai_ids:
            raise PermissionError("voice_admin_required")
        if not all(isinstance(value, str) and value.strip()
                   for value in (conversation_id, target_ai_id)):
            raise ValueError("invalid_voice_target")
        members = conversations.get(conversation_id)
        if not members or acting_ai_id not in members or target_ai_id not in members:
            raise PermissionError("voice_room_membership_required")
        if acting_ai_id == target_ai_id:
            raise ValueError("admin_cannot_mute_self")
        key = (conversation_id, target_ai_id)
        with self._lock:
            if muted:
                self._muted.add(key)
            else:
                self._muted.discard(key)
        return {"conversationId": conversation_id, "targetAiId": target_ai_id,
                "muted": muted}
