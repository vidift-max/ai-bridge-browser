"""Authorization and durable, expiring policy state for Messenger voice controls.

This server-side policy does not capture, transmit, or physically mute audio.
"""
import time
from threading import RLock


class VoiceRoomControl:
    DEFAULT_MUTE_SECONDS = 300
    MAX_MUTE_SECONDS = 3600

    def __init__(self, admin_ai_ids, store=None, clock=None):
        if not isinstance(admin_ai_ids, (set, frozenset, list, tuple)):
            raise ValueError("invalid_voice_admin_ids")
        normalized = {item.strip() for item in admin_ai_ids
                      if isinstance(item, str) and item.strip()}
        if len(normalized) != len(admin_ai_ids):
            raise ValueError("invalid_voice_admin_ids")
        self._admin_ai_ids = frozenset(normalized)
        self._store = store
        self._clock = clock or time.time
        self._muted = {}
        self._lock = RLock()
        if self._store is not None:
            for row in self._store.load_active_voice_mutes(self._clock()):
                self._muted[(row["conversation_id"], row["ai_id"])] = (
                    row["muted_by_ai_id"], row["expires_at"])

    def mute(self, acting_ai_id, conversation_id, target_ai_id, conversations,
             duration_seconds=DEFAULT_MUTE_SECONDS):
        return self._set_muted(True, acting_ai_id, conversation_id,
                               target_ai_id, conversations, duration_seconds)

    def unmute(self, acting_ai_id, conversation_id, target_ai_id, conversations):
        return self._set_muted(False, acting_ai_id, conversation_id,
                               target_ai_id, conversations)

    def is_muted(self, conversation_id, ai_id):
        with self._lock:
            self._expire_locked()
            return (conversation_id, ai_id) in self._muted

    def muted_participants(self, conversation_id):
        with self._lock:
            self._expire_locked()
            return frozenset(ai_id for room_id, ai_id in self._muted
                             if room_id == conversation_id)

    def _expire_locked(self):
        now = self._clock()
        expired = [key for key, value in self._muted.items()
                   if value[1] <= now]
        for conversation_id, ai_id in expired:
            self._muted.pop((conversation_id, ai_id), None)
            if self._store is not None:
                self._store.delete_voice_mute(conversation_id, ai_id)

    def _set_muted(self, muted, acting_ai_id, conversation_id,
                   target_ai_id, conversations, duration_seconds=None):
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
            self._expire_locked()
            if muted:
                if (isinstance(duration_seconds, bool) or
                        not isinstance(duration_seconds, int) or
                        duration_seconds < 1 or
                        duration_seconds > self.MAX_MUTE_SECONDS):
                    raise ValueError("invalid_voice_mute_duration")
                expires_at = self._clock() + duration_seconds
                self._muted[key] = (acting_ai_id, expires_at)
                if self._store is not None:
                    self._store.save_voice_mute(
                        conversation_id, target_ai_id, acting_ai_id, expires_at)
            else:
                self._muted.pop(key, None)
                if self._store is not None:
                    self._store.delete_voice_mute(conversation_id, target_ai_id)
                expires_at = None
        return {"conversationId": conversation_id, "targetAiId": target_ai_id,
                "muted": muted, "expiresAt": expires_at}
