package com.vidiftmax.aibridgebrowser;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.regex.Pattern;

/** Binds updater assets to one stable GitHub Release tag and rejects ambiguous assets. */
public final class UpdateReleasePolicy {
    private static final Pattern TAG = Pattern.compile("[A-Za-z0-9][A-Za-z0-9._-]{0,127}");

    private UpdateReleasePolicy() {}

    public static boolean isStableRelease(JSONObject release) {
        if (release == null || !release.has("draft") || !release.has("prerelease")) return false;
        if (release.optBoolean("draft", true) || release.optBoolean("prerelease", true)) return false;
        return isValidTag(release.opt("tag_name"));
    }

    public static String findUniqueAssetUrl(JSONArray assets, String expectedName, String tagName) {
        if (assets == null || expectedName == null || !isValidTag(tagName)) return null;
        JSONObject match = null;
        for (int i = 0; i < assets.length(); i++) {
            JSONObject asset = assets.optJSONObject(i);
            if (asset == null || !expectedName.equals(asset.optString("name"))) continue;
            if (match != null) return null;
            match = asset;
        }
        if (match == null || !"uploaded".equals(match.optString("state"))) return null;
        Object size = match.opt("size");
        if (!(size instanceof Integer || size instanceof Long) || ((Number) size).longValue() <= 0) return null;
        String url = match.optString("browser_download_url", "");
        if (!UpdateUrlPolicy.isOfficialReleaseAssetUrl(url, tagName, expectedName)) return null;
        return url;
    }

    public static boolean isValidTag(Object value) {
        return value instanceof String && TAG.matcher((String) value).matches();
    }
}
