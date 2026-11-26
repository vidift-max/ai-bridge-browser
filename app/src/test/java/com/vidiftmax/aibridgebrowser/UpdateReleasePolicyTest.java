package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;

import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;

public class UpdateReleasePolicyTest {
    private static final String TAG = "v1.2.3";
    private static final String APK =
            "https://github.com/vidift-max/ai-bridge-browser/releases/download/v1.2.3/app-release.apk";
    private static final String MANIFEST =
            "https://github.com/vidift-max/ai-bridge-browser/releases/download/v1.2.3/ai-bridge-update.json";

    private JSONObject release() throws Exception {
        return new JSONObject().put("draft", false).put("prerelease", false).put("tag_name", TAG);
    }

    private JSONObject asset(String name, String url) throws Exception {
        return new JSONObject().put("name", name).put("state", "uploaded")
                .put("size", 1234).put("browser_download_url", url);
    }

    @Test public void acceptsOnlyStableReleaseWithValidTag() throws Exception {
        assertTrue(UpdateReleasePolicy.isStableRelease(release()));
        assertFalse(UpdateReleasePolicy.isStableRelease(release().put("draft", true)));
        assertFalse(UpdateReleasePolicy.isStableRelease(release().put("prerelease", true)));
        assertFalse(UpdateReleasePolicy.isStableRelease(release().put("tag_name", "../latest")));
        assertFalse(UpdateReleasePolicy.isStableRelease(new JSONObject().put("tag_name", TAG)));
        assertFalse(UpdateReleasePolicy.isStableRelease(null));
    }

    @Test public void rejectsCoercedReleaseFlagsAndTagTypes() throws Exception {
        assertFalse(UpdateReleasePolicy.isStableRelease(
                release().put("draft", "false")));
        assertFalse(UpdateReleasePolicy.isStableRelease(
                release().put("prerelease", 0)));
        assertFalse(UpdateReleasePolicy.isStableRelease(
                release().put("tag_name", 123)));
    }

    @Test public void returnsUniqueUploadedManifestAndApkBoundToReleaseTag() throws Exception {
        JSONArray assets = new JSONArray()
                .put(asset("ai-bridge-update.json", MANIFEST))
                .put(asset("app-release.apk", APK));
        assertEquals(MANIFEST, UpdateReleasePolicy.findUniqueAssetUrl(
                assets, "ai-bridge-update.json", TAG));
        assertEquals(APK, UpdateReleasePolicy.findUniqueAssetUrl(
                assets, "app-release.apk", TAG));
    }

    @Test public void rejectsMissingDuplicateOrUnuploadedAssets() throws Exception {
        JSONArray missing = new JSONArray().put(asset("app-release.apk", APK));
        assertNull(UpdateReleasePolicy.findUniqueAssetUrl(missing, "ai-bridge-update.json", TAG));
        JSONArray duplicate = new JSONArray().put(asset("app-release.apk", APK))
                .put(asset("app-release.apk", APK));
        assertNull(UpdateReleasePolicy.findUniqueAssetUrl(duplicate, "app-release.apk", TAG));
        JSONObject unuploaded = asset("app-release.apk", APK).put("state", "new");
        assertNull(UpdateReleasePolicy.findUniqueAssetUrl(
                new JSONArray().put(unuploaded), "app-release.apk", TAG));
    }

    @Test public void rejectsWrongTagWrongPathAndInvalidAssetMetadata() throws Exception {
        assertNull(UpdateReleasePolicy.findUniqueAssetUrl(
                new JSONArray().put(asset("app-release.apk",
                        "https://github.com/vidift-max/ai-bridge-browser/releases/download/v9.9.9/app-release.apk")),
                "app-release.apk", TAG));
        assertNull(UpdateReleasePolicy.findUniqueAssetUrl(
                new JSONArray().put(asset("app-release.apk",
                        "https://github.com/attacker/ai-bridge-browser/releases/download/v1.2.3/app-release.apk")),
                "app-release.apk", TAG));
        assertNull(UpdateReleasePolicy.findUniqueAssetUrl(
                new JSONArray().put(asset("app-release.apk", APK).put("size", 0)),
                "app-release.apk", TAG));
        assertNull(UpdateReleasePolicy.findUniqueAssetUrl(
                new JSONArray().put(asset("app-release.apk", APK).put("size", "1234")),
                "app-release.apk", TAG));
        assertNull(UpdateReleasePolicy.findUniqueAssetUrl(
                new JSONArray().put(asset("app-release.apk", APK)),
                "app-release.apk", "../v1.2.3"));
    }

    @Test public void rejectsCoercedAssetMetadataTypes() throws Exception {
        JSONObject badState = asset("app-release.apk", APK).put("state", true);
        JSONObject badName = asset("app-release.apk", APK).put("name", 42);
        JSONObject badUrl = asset("app-release.apk", APK).put("browser_download_url", 42);
        assertNull(UpdateReleasePolicy.findUniqueAssetUrl(
                new JSONArray().put(badState), "app-release.apk", TAG));
        assertNull(UpdateReleasePolicy.findUniqueAssetUrl(
                new JSONArray().put(badName), "app-release.apk", TAG));
        assertNull(UpdateReleasePolicy.findUniqueAssetUrl(
                new JSONArray().put(badUrl), "app-release.apk", TAG));
    }

    @Test public void exposesValidatedAssetSizeAlongsideOfficialUrl() throws Exception {
        JSONArray assets = new JSONArray().put(asset("app-release.apk", APK).put("size", 5678));
        UpdateReleasePolicy.AssetMetadata metadata =
                UpdateReleasePolicy.findUniqueAsset(assets, "app-release.apk", TAG);
        assertNotNull(metadata);
        assertEquals(APK, metadata.url);
        assertEquals(5678L, metadata.sizeBytes);
    }

    @Test public void rejectsInvalidSizeWhenReadingAssetMetadata() throws Exception {
        JSONArray zero = new JSONArray().put(asset("app-release.apk", APK).put("size", 0));
        JSONArray text = new JSONArray().put(asset("app-release.apk", APK).put("size", "5678"));
        assertNull(UpdateReleasePolicy.findUniqueAsset(zero, "app-release.apk", TAG));
        assertNull(UpdateReleasePolicy.findUniqueAsset(text, "app-release.apk", TAG));
    }

    @Test public void rejectsMalformedAssetEntries() throws Exception {
        JSONArray assets = new JSONArray().put(JSONObject.NULL)
                .put(new JSONObject().put("name", "app-release.apk"));
        assertNull(UpdateReleasePolicy.findUniqueAssetUrl(assets, "app-release.apk", TAG));
        assertNull(UpdateReleasePolicy.findUniqueAssetUrl(null, "app-release.apk", TAG));
    }
}
