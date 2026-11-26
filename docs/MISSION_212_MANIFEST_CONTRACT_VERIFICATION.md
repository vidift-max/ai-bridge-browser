# Mission 212 — strict updater manifest contract verification

## Scope
Verify the exact JSON contract consumed by `UpdateCenterActivity` and `UpdateManifestPolicy`. Active AI scope remains AI-01 and AI-02 only. No AI-03 activation.

## Ten engineering rounds
1. Re-read the M211 PR, current updater parser, and fail-closed policy.
2. Confirm the six manifest fields consumed by the Android updater: packageName, versionCode, versionName, apkAssetName, sha256, notes.
3. Identify the serialization gap: M211 tests exercised manifest construction but did not test the actual file writer/read-back path.
4. Correct the manifest writer to append a real newline, then parse the emitted file as JSON.
5. Add a strict schema validator that rejects unknown/missing fields, wrong package/asset, invalid version metadata, non-string notes, and malformed SHA-256.
6. Reject Python bool as versionCode (bool is an int subclass); require an actual positive integer.
7. Add serialization round-trip and newline regression tests.
8. Add negative tests for schema drift, package/asset mismatch, invalid version code, and malformed hash.
9. Ensure Android CI runs for this mission branch; keep signed release job manual and gated.
10. Record the release boundary and evidence requirements; open a draft PR without merging or publishing.

## Acceptance / safety
- Manifest schema matches the fields read by the Android updater.
- Generator output must be valid UTF-8 JSON, parse successfully, and end with a normal newline.
- SHA-256 is lowercase hexadecimal, exactly 64 characters.
- Package and APK asset names are fixed to the Android updater contract.
- No signing keys, passwords, or other secrets are read, created, changed, or logged.
- No Release is published; no APK is installed; no updater activation is claimed.
- The updater remains blocked from offering an update until a stable GitHub Release contains the signed APK and manifest, and the installed certificate continuity check passes.

## Current state
Implementation committed to `feat/mission-212-manifest-contract-verification`. CI and PR validation are pending. Expected base: `feat/mission-211-release-manifest-gate`.
