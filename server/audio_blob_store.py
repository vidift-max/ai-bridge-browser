"""Local, bounded storage primitive for authenticated Messenger audio attachments.

This module is intentionally not wired to HTTP yet. Authorization and conversation
ownership must be enforced by the API layer before any object is exposed.
"""
from __future__ import annotations

import hashlib
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path


MAX_AUDIO_BYTES = 5 * 1024 * 1024
_OBJECT_ID = re.compile(r"^[0-9a-f]{32}$")

# Signature-based allowlist: MIME headers alone are never trusted.
_SIGNATURES = {
    "audio/ogg": lambda b: b.startswith(b"OggS"),
    "audio/webm": lambda b: b.startswith(b"\x1aE\xdf\xa3"),
    "audio/wav": lambda b: len(b) >= 12 and b.startswith(b"RIFF") and b[8:12] == b"WAVE",
    "audio/mpeg": lambda b: b.startswith(b"ID3") or (
        len(b) >= 2 and b[0] == 0xFF and (b[1] & 0xE0) == 0xE0
    ),
    "audio/mp4": lambda b: len(b) >= 12 and b[4:8] == b"ftyp",
}


@dataclass(frozen=True)
class StoredAudio:
    object_id: str
    content_type: str
    size: int
    sha256: str


class AudioBlobStore:
    """Stores opaque audio blobs under a dedicated local directory."""

    def __init__(self, root: str | os.PathLike[str], max_bytes: int = MAX_AUDIO_BYTES):
        if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or not 1 <= max_bytes <= MAX_AUDIO_BYTES:
            raise ValueError("invalid_audio_size_limit")
        self.root = Path(root).expanduser().absolute()
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink() or not self.root.is_dir():
            raise ValueError("unsafe_audio_storage_root")
        self.max_bytes = max_bytes

    @staticmethod
    def _verified_type(data: bytes, declared_type: str) -> str:
        if not isinstance(data, bytes) or not data:
            raise ValueError("empty_audio")
        matches = [mime for mime, check in _SIGNATURES.items() if check(data)]
        if len(matches) != 1 or declared_type not in matches:
            raise ValueError("unsupported_or_mismatched_audio_type")
        return matches[0]

    def _object_path(self, object_id: str, create_parent: bool = False) -> Path:
        if not isinstance(object_id, str) or not _OBJECT_ID.fullmatch(object_id):
            raise ValueError("invalid_audio_object_id")
        parent = self.root / object_id[:2]
        if create_parent:
            parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if parent.is_symlink() or not parent.is_dir():
            raise ValueError("unsafe_audio_object_directory")
        path = parent / object_id
        if path.is_symlink():
            raise ValueError("unsafe_audio_object_path")
        return path

    def save(self, data: bytes, declared_type: str) -> StoredAudio:
        verified_type = self._verified_type(data, declared_type)
        if len(data) > self.max_bytes:
            raise ValueError("audio_too_large")
        object_id = uuid.uuid4().hex
        path = self._object_path(object_id, create_parent=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(path, flags, 0o600)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            try:
                path.unlink(missing_ok=True)
            finally:
                raise
        return StoredAudio(object_id, verified_type, len(data), hashlib.sha256(data).hexdigest())

    def read(self, object_id: str) -> bytes:
        path = self._object_path(object_id)
        if not path.is_file():
            raise FileNotFoundError("audio_object_not_found")
        data = path.read_bytes()
        if len(data) > self.max_bytes:
            raise ValueError("stored_audio_exceeds_limit")
        return data

    def delete(self, object_id: str) -> bool:
        path = self._object_path(object_id)
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return False
