import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from create_android_update_manifest import (
    create_manifest, parse_badging, validate_manifest, write_manifest,
)


BADGING = (
    "package: name='com.vidiftmax.aibridgebrowser' "
    "versionCode='7' versionName='1.2.3'\n"
    "sdkVersion:'29'\n"
)


class AndroidUpdateManifestTests(unittest.TestCase):
    def _manifest(self, directory):
        apk = Path(directory) / "app-release.apk"
        apk.write_bytes(b"synthetic-apk-bytes")
        return apk, create_manifest(apk, BADGING)

    def test_manifest_uses_real_apk_hash_and_android_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            apk, manifest = self._manifest(directory)
            self.assertEqual("com.vidiftmax.aibridgebrowser", manifest["packageName"])
            self.assertEqual(7, manifest["versionCode"])
            self.assertEqual("1.2.3", manifest["versionName"])
            self.assertEqual("app-release.apk", manifest["apkAssetName"])
            self.assertEqual(hashlib.sha256(apk.read_bytes()).hexdigest(), manifest["sha256"])
            self.assertEqual(64, len(manifest["sha256"]))

    def test_writer_outputs_valid_json_with_real_newline_and_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            _, manifest = self._manifest(directory)
            output = Path(directory) / "ai-bridge-update.json"
            write_manifest(output, manifest)
            raw = output.read_text(encoding="utf-8")
            self.assertTrue(raw.endswith("\n"))
            self.assertFalse(raw.endswith("\\n"))
            self.assertEqual(manifest, json.loads(raw))

    def test_rejects_schema_drift_and_wrong_apk_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            _, manifest = self._manifest(directory)
            with self.assertRaisesRegex(ValueError, "update_manifest_schema_mismatch"):
                validate_manifest({**manifest, "unexpected": True})
            with self.assertRaisesRegex(ValueError, "unexpected_apk_asset_name"):
                validate_manifest({**manifest, "apkAssetName": "other.apk"})

    def test_rejects_invalid_version_hash_and_wrong_application_id(self):
        with tempfile.TemporaryDirectory() as directory:
            _, manifest = self._manifest(directory)
            with self.assertRaisesRegex(ValueError, "invalid_android_version_code"):
                validate_manifest({**manifest, "versionCode": True})
            with self.assertRaisesRegex(ValueError, "invalid_apk_sha256"):
                validate_manifest({**manifest, "sha256": "not-a-hash"})
            with self.assertRaisesRegex(ValueError, "unexpected_application_id"):
                validate_manifest({**manifest, "packageName": "com.example.other"})

    def test_rejects_wrong_application_id_in_aapt(self):
        with self.assertRaisesRegex(ValueError, "unexpected_application_id"):
            parse_badging("package: name='com.example.other' versionCode='2' versionName='2.0'")

    def test_rejects_missing_or_invalid_version_metadata(self):
        with self.assertRaisesRegex(ValueError, "aapt_badging_package_metadata_missing"):
            parse_badging("sdkVersion:'29'")
        with self.assertRaisesRegex(ValueError, "invalid_android_version_metadata"):
            parse_badging(
                "package: name='com.vidiftmax.aibridgebrowser' "
                "versionCode='0' versionName=''"
            )

    def test_rejects_missing_or_empty_apk(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "empty.apk"
            apk.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "release_apk_missing_or_empty"):
                create_manifest(apk, BADGING)


if __name__ == "__main__":
    unittest.main()
