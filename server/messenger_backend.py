from dataclasses import dataclass
import hashlib
import secrets
from functools import wraps
from threading import Condition, RLock
from typing import Dict, List, Set, Tuple
import time
from datetime import datetime, timedelta, timezone
from server.auth import Authenticator
from server.sqlite_store import SQLiteMessengerStore
from server.audio_blob_store import AudioBlobStore
from server.presence_service import PresenceService
from server.identity_directory import IdentityDirectory
from server.retention_policy import (MESSAGE_NORMAL, MESSAGE_MISSION, CONVERSATION_GROUP,
                                     expires_at, is_expired, normalize_message_kind, normalize_conversation_kind)

def _synchronized(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._lock: