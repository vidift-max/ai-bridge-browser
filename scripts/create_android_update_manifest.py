#!/usr/bin/env python3
"""Create the strict JSON manifest consumed by the Android in-app updater."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


EXPECTED_PACKAGE = "com.vidiftmax.aibridgebrowser"
EXPECTED_APK_ASSET = "app-release.apk"
PACKAGE_LINE = re.compile(
    r"^package:\s+name='([^']+)'\s+versionCode='([0-9]+)'\s+versionName='([^']*)'",
    re.MULTILINE,
)


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


def create_manifest(apk_path: str | Path, badging_output: str) -> dict:
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
    output = Path(args.output)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\\n",
                      encoding="utf-8")
    # Read-after-write validation prevents uploading malformed metadata.
    parsed = json.loads(output.read_text(encoding="utf-8"))
    if parsed != manifest or not re.fullmatch(r"[a-f0-9]{64}", parsed["sha256"]):
        raise ValueError("update_manifest_roundtrip_validation_failed")
    print("UPDATE_MANIFEST_VALID=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
