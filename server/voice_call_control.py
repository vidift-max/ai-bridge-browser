"""Authenticated one-to-one call lifecycle and WebRTC signaling policy.

This module carries signaling metadata only. It never captures or relays media.
"""
import json
import re
import time
import uuid
from threading import RLock


class VoiceCallControl:
    RING_TIMEOUT_SECONDS = 45
    MAX_SIGNAL_BYTES = 24000
    SIGNAL_KINDS = frozenset({"OFFER", "ANSWER", "ICE_CANDIDATE", "ICE_COMPLETE"})

    def __init__(self, store, clock=None, id_factory=None):
        self._store = store
        self._clock = clock or time.time
        self._id_factory = id_factory or (lambda: str(uuid.uuid4()))
        self._lock = RLock()

    def create(self, caller_ai_id, callee_ai_id, conversation_id, conversations,
               conversation_kinds):
        self._validate_ids(caller_ai_id, callee_ai_id, conversation_id)
        if caller_ai_id == callee_ai_id:
            raise ValueError("voice_call_self_target")
        members = conversations.get(conversation_id)
        if not members or members != {caller_ai_id, callee_ai_id}:
            raise PermissionError("private_conversation_membership_required")
        if conversation_kinds.get(conversation_id) != "PRIVATE":
            raise PermissionError("private_conversation_required")
        now = self._clock()
        with self._lock:
            active = self._store.find_active_voice_call(conversation_id)
            if active:
                if active["caller_ai_id"] == caller_ai_id and active["callee_ai_id"] == callee_ai_id:
                    return self._public(active)
                raise RuntimeError("voice_call_busy")
            call = {
                "call_id": self._id_factory(), "conversation_id": conversation_id,
                "caller_ai_id": caller_ai_id, "callee_ai_id": callee_ai_id,
                "state": "RINGING", "created_at": now,
                "expires_at": now + self.RING_TIMEOUT_SECONDS, "updated_at": now,
            }
            self._store.save_voice_call(call)
            return self._public(call)

    def active_for_conversation(self, acting_ai_id, conversation_id):
        call = self._store.find_active_voice_call(conversation_id)
        if call is None:
            return None
        self._authorize(call, acting_ai_id)
        with self._lock:
            return self._public(self._expire_if_needed(call))

    def get(self, acting_ai_id, call_id):
        call = self._required_call(call_id)
        self._authorize(call, acting_ai_id)
        with self._lock:
            call = self._expire_if_needed(call)
            return self._public(call)

    def transition(self, acting_ai_id, call_id, action):
        call = self._required_call(call_id)
        self._authorize(call, acting_ai_id)
        allowed = {
            "accept": ("RINGING", "callee", "ACCEPTED"),
            "reject": ("RINGING", "callee", "REJECTED"),
            "cancel": ("RINGING", "caller", "CANCELLED"),
            "end": (("ACCEPTED", "CONNECTING", "CONNECTED"), "either", "ENDED"),
        }
        if action not in allowed:
            raise ValueError("invalid_voice_call_action")
        expected, actor, target = allowed[action]
        with self._lock:
            call = self._expire_if_needed(call)
            if call["state"] == target:
                return self._public(call)
            if call["state"] not in ((expected,) if isinstance(expected, str) else expected):
                raise RuntimeError("invalid_voice_call_transition")
            if actor == "caller" and acting_ai_id != call["caller_ai_id"]:
                raise PermissionError("voice_call_caller_required")
            if actor == "callee" and acting_ai_id != call["callee_ai_id"]:
                raise PermissionError("voice_call_callee_required")
            call["state"] = target
            call["updated_at"] = self._clock()
            call["expires_at"] = call["updated_at"]
            self._store.update_voice_call(call)
            return self._public(call)

    def set_connecting(self, acting_ai_id, call_id):
        call = self._required_call(call_id)
        self._authorize(call, acting_ai_id)
        with self._lock:
            call = self._expire_if_needed(call)
            if call["state"] == "CONNECTING":
                return self._public(call)
            if call["state"] != "ACCEPTED":
                raise RuntimeError("invalid_voice_call_transition")
            call["state"] = "CONNECTING"
            call["updated_at"] = self._clock()
            self._store.update_voice_call(call)
            return self._public(call)

    def set_connected(self, acting_ai_id, call_id):
        call = self._required_call(call_id)
        self._authorize(call, acting_ai_id)
        with self._lock:
            call = self._expire_if_needed(call)
            if call["state"] == "CONNECTED":
                return self._public(call)
            if call["state"] not in ("ACCEPTED", "CONNECTING"):
                raise RuntimeError("invalid_voice_call_transition")
            call["state"] = "CONNECTED"
            call["updated_at"] = self._clock()
            self._store.update_voice_call(call)
            return self._public(call)

    def add_signal(self, acting_ai_id, call_id, kind, payload):
        call = self._required_call(call_id)
        self._authorize(call, acting_ai_id)
        if kind not in self.SIGNAL_KINDS or not isinstance(payload, dict):
            raise ValueError("invalid_voice_signal")
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
        if len(encoded.encode("utf-8")) > self.MAX_SIGNAL_BYTES:
            raise ValueError("voice_signal_too_large")
        if kind in ("OFFER", "ANSWER"):
            if set(payload) != {"type", "sdp"} or payload.get("type") != kind.lower():
                raise ValueError("invalid_voice_session_description")
            sdp = payload.get("sdp")
            if not isinstance(sdp, str) or not sdp.strip() or len(sdp) > 18000:
                raise ValueError("invalid_voice_session_description")
        elif kind == "ICE_CANDIDATE":
            if set(payload) - {"candidate", "sdpMid", "sdpMLineIndex", "usernameFragment"}:
                raise ValueError("invalid_ice_candidate")
            if not isinstance(payload.get("candidate"), str) or len(payload["candidate"]) > 4096:
                raise ValueError("invalid_ice_candidate")
        elif payload:
            raise ValueError("invalid_ice_complete")
        with self._lock:
            call = self._expire_if_needed(call)
            if call["state"] not in ("ACCEPTED", "CONNECTING", "CONNECTED"):
                raise RuntimeError("voice_call_not_accepted")
            return self._store.append_voice_signal(call_id, acting_ai_id, kind, payload, self._clock())

    def pending_signals(self, acting_ai_id, call_id, after_id=0, limit=100):
        call = self._required_call(call_id)
        self._authorize(call, acting_ai_id)
        if isinstance(after_id, bool) or not isinstance(after_id, int) or after_id < 0:
            raise ValueError("invalid_voice_signal_cursor")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1 or limit > 100:
            raise ValueError("invalid_voice_signal_limit")
        with self._lock:
            call = self._expire_if_needed(call)
            return self._store.load_voice_signals(call_id, acting_ai_id, after_id, limit)

    def _required_call(self, call_id):
        if not isinstance(call_id, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,80}", call_id):
            raise ValueError("invalid_voice_call_id")
        call = self._store.get_voice_call(call_id)
        if call is None:
            raise ValueError("voice_call_not_found")
        return call

    @staticmethod
    def _validate_ids(caller, callee, conversation):
        for value in (caller, callee):
            if not isinstance(value, str) or not re.fullmatch(r"AI-[A-Z0-9][A-Z0-9-]{0,62}", value):
                raise ValueError("invalid_voice_participant")
        if not isinstance(conversation, str) or not conversation.strip() or len(conversation) > 200:
            raise ValueError("invalid_voice_conversation")

    @staticmethod
    def _authorize(call, ai_id):
        if ai_id not in (call["caller_ai_id"], call["callee_ai_id"]):
            raise PermissionError("voice_call_participant_required")

    def _expire_if_needed(self, call):
        if call["state"] == "RINGING" and call["expires_at"] <= self._clock():
            call["state"] = "TIMED_OUT"
            call["updated_at"] = self._clock()
            self._store.update_voice_call(call)
        return call

    @staticmethod
    def _public(call):
        return {key: call[key] for key in (
            "call_id", "conversation_id", "caller_ai_id", "callee_ai_id",
            "state", "created_at", "expires_at", "updated_at")}
