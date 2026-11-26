package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.json.JSONObject;
import org.junit.Test;

public class UpdateManifestPolicyTest {
    private static final String HASH = "a".repeat(64);
    private static final String URL =
            "https://github.com/vidift-max/ai-bridge-browser/releases/download/v1.0/app-release.apk";

    private JSONObject validManifest() throws Exception {
        return new JSONObject()
                .put("packageName", "com.vidiftmax.aibridgebrowser")
                .put("versionCode", 7)
                .put("versionName", "1.2.3")
                .put("apkAssetName", "app-release.apk")
                .put("sha256", HASH)
                .put("notes", "Atualização oficial.");
    }

    @Test public void acceptsExactGeneratorManifestShape() throws Exception {
        assertTrue(UpdateManifestPolicy.isManifestShapeEligible(validManifest()));
    }

    @Test public void rejectsMissingAndUnexpectedManifestFields() throws Exception {
        JSONObject missing = validManifest();
        missing.remove("notes");
        assertFalse(UpdateManifestPolicy.isManifestShapeEligible(missing));
        JSONObject extra = validManifest().put("debug", true);
        assertFalse(UpdateManifestPolicy.isManifestShapeEligible(extra));
    }

    @Test public void rejectsCoercedOrInvalidVersionAndWrongTypes() throws Exception {
        assertFalse(UpdateManifestPolicy.isManifestShapeEligible(
                validManifest().put("versionCode", "7")));
        assertFalse(UpdateManifestPolicy.isManifestShapeEligible(
                validManifest().put("versionCode", true)));
        assertFalse(UpdateManifestPolicy.isManifestShapeEligible(
                validManifest().put("versionCode", 0)));
        assertFalse(UpdateManifestPolicy.isManifestShapeEligible(
                validManifest().put("versionName", "  ")));
        assertFalse(UpdateManifestPolicy.isManifestShapeEligible(
                validManifest().put("notes", 123)));
    }

    @Test public void rejectsWrongPackageAssetAndMalformedHash() throws Exception {
        assertFalse(UpdateManifestPolicy.isManifestShapeEligible(
                validManifest().put("packageName", "com.example.other")));
        assertFalse(UpdateManifestPolicy.isManifestShapeEligible(
                validManifest().put("apkAssetName", "app-debug.apk")));
        assertFalse(UpdateManifestPolicy.isManifestShapeEligible(
                validManifest().put("sha256", "not-a-hash")));
        assertFalse(UpdateManifestPolicy.isManifestShapeEligible(
                validManifest().put("sha256", HASH.toUpperCase(java.util.Locale.ROOT))));
    }

    @Test public void acceptsHigherVersionWithExpectedPackageAssetHashAndOfficialUrl() {
        assertTrue(UpdateManifestPolicy.isEligible(2, 1,
                "com.vidiftmax.aibridgebrowser", "com.vidiftmax.aibridgebrowser",
                "app-release.apk", "app-release.apk", HASH, URL));
    }

    @Test public void rejectsSameOrOlderVersion() {
        assertFalse(UpdateManifestPolicy.isEligible(1, 1,
                "com.vidiftmax.aibridgebrowser", "com.vidiftmax.aibridgebrowser",
                "app-release.apk", "app-release.apk", HASH, URL));
        assertFalse(UpdateManifestPolicy.isEligible(0, 1,
                "com.vidiftmax.aibridgebrowser", "com.vidiftmax.aibridgebrowser",
                "app-release.apk", "app-release.apk", HASH, URL));
    }

    @Test public void rejectsDifferentPackageOrAssetName() {
        assertFalse(UpdateManifestPolicy.isEligible(2, 1,
                "com.example.other", "com.vidiftmax.aibridgebrowser",
                "app-release.apk", "app-release.apk", HASH, URL));
        assertFalse(UpdateManifestPolicy.isEligible(2, 1,
                "com.vidiftmax.aibridgebrowser", "com.vidiftmax.aibridgebrowser",
                "debug.apk", "app-release.apk", HASH, URL));
    }

    @Test public void rejectsMalformedHashAndNonOfficialDownloadOrigin() {
        assertFalse(UpdateManifestPolicy.isEligible(2, 1,
                "com.vidiftmax.aibridgebrowser", "com.vidiftmax.aibridgebrowser",
                "app-release.apk", "app-release.apk", "xyz", URL));
        assertFalse(UpdateManifestPolicy.isEligible(2, 1,
                "com.vidiftmax.aibridgebrowser", "com.vidiftmax.aibridgebrowser",
                "app-release.apk", "app-release.apk", HASH,
                "https://example.com/app-release.apk"));
        assertFalse(UpdateManifestPolicy.isEligible(2, 1,
                "com.vidiftmax.aibridgebrowser", "com.vidiftmax.aibridgebrowser",
                "app-release.apk", "app-release.apk", HASH,
                "http://github.com/vidift-max/ai-bridge-browser/releases/download/v1/app-release.apk"));
    }

    @Test public void rejectsMissingMetadata() {
        assertFalse(UpdateManifestPolicy.isEligible(2, 1, null,
                "com.vidiftmax.aibridgebrowser", "app-release.apk", "app-release.apk", HASH, URL));
        assertFalse(UpdateManifestPolicy.isEligible(2, 1,
                "com.vidiftmax.aibridgebrowser", "com.vidiftmax.aibridgebrowser",
                "app-release.apk", "app-release.apk", HASH, null));
    }
}
