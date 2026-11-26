package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class UpdateManifestPolicyTest {
    private static final String HASH = "a".repeat(64);
    private static final String URL =
            "https://github.com/vidift-max/ai-bridge-browser/releases/download/v1.0/app-release.apk";

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
