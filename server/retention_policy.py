from __future__ import annotations

ONE_HOUR_SECONDS = 60 * 60
ONE_DAY_SECONDS = 24 * ONE_HOUR_SECONDS
MESSAGE_NORMAL = "NORMAL"
MESSAGE_MISSION = "MISSION"
CONVERSATION_GROUP = "GROUP"
CONVERSATION_PRIVATE = "PRIVATE"

def normalize_message_kind(kind: str) -> str:
    return MESSAGE_MISSION if kind == MESSAGE_MISSION else MESSAGE_NORMAL

def normalize_conversation_kind(kind: str) -> str:
    return CONVERSATION_PRIVATE if kind == CONVERSATION_PRIVATE else CONVERSATION_GROUP

def retention_seconds(message_kind: str, conversation_kind: str) -> int:
    if normalize_message_kind(message_kind) == MESSAGE_MISSION:
        return ONE_DAY_SECONDS
    if normalize_conversation_kind(conversation_kind) == CONVERSATION_PRIVATE:
        return ONE_DAY_SECONDS
    return ONE_HOUR_SECONDS

def expires_at(created_at_epoch_seconds: float, message_kind: str, conversation_kind: str) -> float:
    if created_at_epoch_seconds <= 0:
        raise ValueError("invalid_message_timestamp")
    return created_at_epoch_seconds + retention_seconds(message_kind, conversation_kind)

def is_expired(created_at_epoch_seconds: float, message_kind: str,
               conversation_kind: str, now_epoch_seconds: float) -> bool:
    if created_at_epoch_seconds <= 0:
        return True
    return now_epoch_seconds >= expires_at(created_at_epoch_seconds, message_kind, conversation_kind)
