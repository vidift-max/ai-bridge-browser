#!/usr/bin/env python3
"""Create and validate the strict JSON manifest consumed by the Android updater."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

EXPECTED_PACKAGE = "com.vidiftmax.aibridgebrowser"
EXPECTED_APK_ASSET = "app-release.apk"
MANIFEST_KEYS = {
    "packageName", "versionCode", "versionName", "apkAssetName", "sha256", "notes"
}
PACKAGE_LINE = re.compile(
    r"^package:\\s+name='([^']+)'\\s+versionCode='([0-9]+)'\\s+versionName='([^']*)'",
    re.MULTILINE,
)
SHA256 = re.compile(r"[a-f0-9]{64}")


def parse_badging(output: str) -> tuple[str, int, str]:
    match = PACKAGE_LINE.search(output)
    if not match:
        raise ValueError("aapt_badging_package_metadata_missing")
    package_name, raw_code, version_name = match.groups()
    version_code = int(raw_code)
    if package_name != EXPECTED_PACKAGE:
        raise ValueError("unexpected_application_id")
    if version_code < 1 or not version_name.strip():
        raise ValueError("invalid_android_version_metadata")
    return package_name, version_code, version_name


def create_manifest(apk_path: str | Path, badging_output: str) -> dict[str, Any]:
    apk = Path(apk_path)
    if not apk.is_file() or apk.stat().st_size <= 0:
        raise ValueError("release_apk_missing_or_empty")
    package_name, version_code, version_name = parse_badging(badging_output)
    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    return {
        "packageName": package_name,
        "versionCode": version_code,
        "versionName": version_name,
        "apkAssetName": EXPECTED_APK_ASSET,
        "sha256": digest,
        "notes": "AI Bridge Browser — versão oficial assinada.",
    }


def validate_manifest(manifest: dict[str, Any]) -> None:
    if set(manifest) != MANIFEST_KEYS:
        raise ValueError("update_manifest_schema_mismatch")
    if manifest["packageName"] != EXPECTED_PACKAGE:
        raise ValueError("unexpected_application_id")
    if manifest["apkAssetName"] != EXPECTED_APK_ASSET:
        raise ValueError("unexpected_apk_asset_name")
    if not isinstance(manifest["versionCode"], int) or manifest["versionCode"] < 1:
        raise ValueError("invalid_android_version_code")
    if not isinstance(manifest["versionName"], str) or not manifest["versionName"].strip():
        raise ValueError("invalid_android_version_name")
    if not isinstance(manifest["notes"], str):
        raise ValueError("invalid_update_notes")
    if not isinstance(manifest["sha256"], str) or not SHA256.fullmatch(manifest["sha256"]):
        raise ValueError("invalid_apk_sha256")


def write_manifest(output_path: str | Path, manifest: dict[str, Any]) -> None:
    validate_manifest(manifest)
    output = Path(output_path)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\\n",
                      encoding="utf-8")
    raw = output.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    validate_manifest(parsed)
    if parsed != manifest or not raw.endswith("\\n"):
        raise ValueError("update_manifest_roundtrip_validation_failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk", required=True)
    parser.add_argument("--aapt", required=True)
    parser.add_argument("--output", default="ai-bridge-update.json")
    args = parser.parse_args()
    completed = subprocess.run(
        [args.aapt, "dump", "badging", args.apk],
        check=True, capture_output=True, text=True,
    )
    manifest = create_manifest(args.apk, completed.stdout)
    write_manifest(args.output, manifest)
    print("UPDATE_MANIFEST_VALID=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
