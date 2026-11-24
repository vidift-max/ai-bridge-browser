import hashlib
import tempfile
import unittest
from pathlib import Path

from server.audio_blob_store import AudioBlobStore, MAX_AUDIO_BYTES


class AudioBlobStoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = AudioBlobStore(self.tmp.name, max_bytes=64)
        self.ogg = b"OggS" + b"\x00" * 20

    def tearDown(self):
        self.tmp.cleanup()

    def test_save_returns_opaque_id_verified_type_size_and_hash(self):
        saved = self.store.save(self.ogg, "audio/ogg")
        self.assertEqual(len(saved.object_id), 32)
        self.assertEqual(saved.content_type, "audio/ogg")
        self.assertEqual(saved.size, len(self.ogg))
        self.assertEqual(saved.sha256, hashlib.sha256(self.ogg).hexdigest())

    def test_read_returns_exact_original_bytes(self):
        saved = self.store.save(self.ogg, "audio/ogg")
        self.assertEqual(self.store.read(saved.object_id), self.ogg)

    def test_rejects_empty_payload(self):
        with self.assertRaisesRegex(ValueError, "empty_audio"):
            self.store.save(b"", "audio/ogg")

    def test_rejects_unknown_signature(self):
        with self.assertRaisesRegex(ValueError, "unsupported_or_mismatched_audio_type"):
            self.store.save(b"not an audio file", "audio/ogg")

    def test_rejects_mime_spoofing(self):
        with self.assertRaisesRegex(ValueError, "unsupported_or_mismatched_audio_type"):
            self.store.save(self.ogg, "audio/mpeg")

    def test_rejects_payload_above_configured_limit(self):
        with self.assertRaisesRegex(ValueError, "audio_too_large"):
            self.store.save(b"OggS" + b"x" * 61, "audio/ogg")

    def test_rejects_path_traversal_and_non_hex_ids(self):
        for object_id in ("../secret", "/etc/passwd", "A" * 32, "g" * 32, ""):
            with self.subTest(object_id=object_id):
                with self.assertRaisesRegex(ValueError, "invalid_audio_object_id"):
                    self.store.read(object_id)

    def test_delete_removes_only_requested_object(self):
        first = self.store.save(self.ogg, "audio/ogg")
        second = self.store.save(self.ogg + b"x", "audio/ogg")
        self.assertTrue(self.store.delete(first.object_id))
        self.assertFalse(self.store.delete(first.object_id))
        self.assertEqual(self.store.read(second.object_id), self.ogg + b"x")

    def test_rejects_symlinked_object_directory(self):
        saved = self.store.save(self.ogg, "audio/ogg")
        object_dir = Path(self.tmp.name) / saved.object_id[:2]
        target = Path(self.tmp.name) / "outside"
        target.mkdir()
        real_dir = Path(self.tmp.name) / "real"
        real_dir.mkdir()
        # Replace the shard directory with a symlink to a directory outside the store.
        for child in object_dir.iterdir():
            child.unlink()
        object_dir.rmdir()
        try:
            object_dir.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("directory symlinks are unavailable on this platform")
        with self.assertRaisesRegex(ValueError, "unsafe_audio_object_directory"):
            self.store.read(saved.object_id)

    def test_constructor_rejects_invalid_size_limits(self):
        for value in (0, -1, MAX_AUDIO_BYTES + 1, True, 1.5):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "invalid_audio_size_limit"):
                    AudioBlobStore(self.tmp.name, max_bytes=value)


if __name__ == "__main__":
    unittest.main()
