# Mission 213 — cross-platform updater manifest contract

## Scope
Make Android reject any update manifest whose JSON shape differs from the strict contract emitted by the Python Release manifest generator. Active account scope remains AI-01 and AI-02; no AI-03 activation.

## Ten engineering rounds
1. Confirm M212 CI completed successfully on final SHA `2eb38df0b0d3470de467a964fa62f15c6cfd51c9`.
2. Inspect the actual fields consumed by `UpdateCenterActivity` and the generator's six-field schema.
3. Identify that the Android parser previously relied on JSONObject coercion and did not reject unknown/missing keys or wrong JSON value types.
4. Add `UpdateManifestPolicy.isManifestShapeEligible` with exact-key, exact-type, package, asset, version and lowercase SHA-256 validation.
5. Reject missing/null values and unknown fields before any manifest values are consumed.
6. Wire `UpdateCenterActivity` to fail closed before reading version metadata.
7. Add Android unit tests for the valid generator-shaped JSON object.
8. Add negative tests for extra/missing/null keys, numeric-string/boolean/zero versionCode, blank version name, wrong package/asset, wrong notes type and malformed/uppercase SHA.
9. Extend CI triggers for this mission's push branch and PRs targeting the M212 branch.
10. Document release boundaries and prepare a draft PR without merge, signing or publication.

## Contract
The exact JSON keys are:
- `packageName` — string, fixed to `com.vidiftmax.aibridgebrowser`
- `versionCode` — positive JSON integer
- `versionName` — non-empty string
- `apkAssetName` — string, fixed to `app-release.apk`
- `sha256` — 64 lowercase hexadecimal characters
- `notes` — string

No extra or missing fields are accepted. This shape validation is followed by the existing version/package/asset/hash/official-origin policy and APK package/certificate verification.

## Safety and release status
- No signing secrets read, created, changed, or transmitted.
- `release-final` remains manual and secret-gated.
- No GitHub Release published; no APK installed; no physical device test claimed.
- The update button must not be treated as operational until a stable Release contains a signed APK and matching manifest and certificate continuity is verified.
