package com.vidiftmax.aibridgebrowser;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.regex.Pattern;

/** Binds updater assets to one stable GitHub Release tag and rejects ambiguous assets. */
public final class UpdateReleasePolicy {
    private static final Pattern TAG = Pattern.compile("[A-Za-z0-9][A-Za-z0-9._-]{0,127}");

    public static final class AssetMetadata {
        public final String url;
        public final long sizeBytes;
        private AssetMetadata(String url, long sizeBytes) {
            this.url = url;
            this.sizeBytes = sizeBytes;
        }
    }

    private UpdateReleasePolicy() {}

    public static boolean isStableRelease(JSONObject release) {
        if (release == null || !(release.opt("draft") instanceof Boolean)
                || !(release.opt("prerelease") instanceof Boolean)) return false;
        if (Boolean.TRUE.equals(release.opt("draft"))
                || Boolean.TRUE.equals(release.opt("prerelease"))) return false;
        return isValidTag(release.opt("tag_name"));
    }

    public static String findUniqueAssetUrl(JSONArray assets, String expectedName, String tagName) {
        AssetMetadata asset = findUniqueAsset(assets, expectedName, tagName);
        return asset == null ? null : asset.url;
    }

    public static AssetMetadata findUniqueAsset(JSONArray assets, String expectedName, String tagName) {
        if (assets == null || expectedName == null || !isValidTag(tagName)) return null;
        JSONObject match = null;
        for (int i = 0; i < assets.length(); i++) {
            JSONObject asset = assets.optJSONObject(i);
            if (asset == null || !(asset.opt("name") instanceof String)
                    || !expectedName.equals(asset.opt("name"))) continue;
            if (match != null) return null;
            match = asset;
        }
        if (match == null || !(match.opt("state") instanceof String)
                || !"uploaded".equals(match.opt("state")) return null;
        Object size = match.opt("size");
        if (!(size instanceof Integer || size instanceof Long)) return null;
        long sizeBytes = ((Number) size).longValue();
        if (sizeBytes <= 0) return null;
        Object rawUrl = match.opt("browser_download_url");
        if (!(rawUrl instanceof String)) return null;
        String url = (String) rawUrl;
        if (!UpdateUrlPolicy.isOfficialReleaseAssetUrl(url, tagName, expectedName)) return null;
        return new AssetMetadata(url, sizeBytes);
    }

    public static boolean isValidTag(Object value) {
        return value instanceof String && TAG.matcher((String) value).matches();
    }
}
