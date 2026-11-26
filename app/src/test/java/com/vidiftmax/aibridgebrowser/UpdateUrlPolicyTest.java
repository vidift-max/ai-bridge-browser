package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class UpdateUrlPolicyTest {
    private static final String OFFICIAL =
            "https://github.com/vidift-max/ai-bridge-browser/releases/download/v1.0/app-release.apk";

    @Test public void acceptsOnlyOfficialReleaseAssetPath() {
        assertTrue(UpdateUrlPolicy.isOfficialReleaseAssetUrl(OFFICIAL));
        assertTrue(UpdateUrlPolicy.isOfficialReleaseAssetUrl(
                "https://github.com/vidift-max/ai-bridge-browser/releases/download/v1.0/ai-bridge-update.json"));
    }

    @Test public void rejectsLookalikeHostsAndOtherRepositories() {
        assertFalse(UpdateUrlPolicy.isOfficialReleaseAssetUrl(
                "https://github.com.evil.example/vidift-max/ai-bridge-browser/releases/download/v1/app-release.apk"));
        assertFalse(UpdateUrlPolicy.isOfficialReleaseAssetUrl(
                "https://evilgithub.com/vidift-max/ai-bridge-browser/releases/download/v1/app-release.apk"));
        assertFalse(UpdateUrlPolicy.isOfficialReleaseAssetUrl(
                "https://github.com/attacker/ai-bridge-browser/releases/download/v1/app-release.apk"));
        assertFalse(UpdateUrlPolicy.isOfficialReleaseAssetUrl(
                "https://github.com/vidift-max/other/releases/download/v1/app-release.apk"));
    }

    @Test public void rejectsUnsafeSchemePortCredentialsAndDecorations() {
        assertFalse(UpdateUrlPolicy.isOfficialReleaseAssetUrl(
                "http://github.com/vidift-max/ai-bridge-browser/releases/download/v1/app-release.apk"));
        assertFalse(UpdateUrlPolicy.isOfficialReleaseAssetUrl(
                "https://github.com:444/vidift-max/ai-bridge-browser/releases/download/v1/app-release.apk"));
        assertFalse(UpdateUrlPolicy.isOfficialReleaseAssetUrl(
                "https://user@github.com/vidift-max/ai-bridge-browser/releases/download/v1/app-release.apk"));
        assertFalse(UpdateUrlPolicy.isOfficialReleaseAssetUrl(
                OFFICIAL + "?redirect=https://evil.example"));
        assertFalse(UpdateUrlPolicy.isOfficialReleaseAssetUrl(OFFICIAL + "#fragment"));
        assertFalse(UpdateUrlPolicy.isOfficialReleaseAssetUrl("not a URL"));
        assertFalse(UpdateUrlPolicy.isOfficialReleaseAssetUrl(null));
    }

    @Test public void allowsOnlyHttpsRedirectsToExactGitHubAssetHosts() {
        assertTrue(UpdateUrlPolicy.isAllowedRedirectUrl("https://github.com/"));
        assertTrue(UpdateUrlPolicy.isAllowedRedirectUrl("https://api.github.com/repos/vidift-max/ai-bridge-browser"));
        assertTrue(UpdateUrlPolicy.isAllowedRedirectUrl("https://objects.githubusercontent.com/signed/object"));
        assertTrue(UpdateUrlPolicy.isAllowedRedirectUrl("https://release-assets.githubusercontent.com/file"));
        assertFalse(UpdateUrlPolicy.isAllowedRedirectUrl("http://objects.githubusercontent.com/file"));
        assertFalse(UpdateUrlPolicy.isAllowedRedirectUrl("https://objects.githubusercontent.com.evil.example/file"));
        assertFalse(UpdateUrlPolicy.isAllowedRedirectUrl("https://evil.example/file"));
        assertFalse(UpdateUrlPolicy.isAllowedRedirectUrl("https://github.com:444/file"));
        assertFalse(UpdateUrlPolicy.isAllowedRedirectUrl("https://user@github.com/file"));
        assertFalse(UpdateUrlPolicy.isAllowedRedirectUrl(null));
    }
}
