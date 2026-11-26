package com.vidiftmax.aibridgebrowser;

import org.json.JSONObject;

import java.util.Iterator;
import java.util.Locale;
import java.util.regex.Pattern;

/** Fail-closed validation for metadata consumed by the in-app updater. */
public final class UpdateManifestPolicy {
    private static final Pattern SHA256 = Pattern.compile("[a-f0-9]{64}");
    private static final String PACKAGE_NAME = "com.vidiftmax.aibridgebrowser";
    private static final String APK_ASSET = "app-release.apk";
    private static final String[] MANIFEST_KEYS = {
            "packageName", "versionCode", "versionName", "apkAssetName", "sha256", "notes"
    };

    private UpdateManifestPolicy() {}

    /** Validates the exact JSON shape emitted by scripts/create_android_update_manifest.py. */
    public static boolean isManifestShapeEligible(JSONObject manifest) {
        if (manifest == null || manifest.length() != MANIFEST_KEYS.length) return false;
        for (String key : MANIFEST_KEYS) {
            if (!manifest.has(key) || manifest.isNull(key)) return false;
        }
        Iterator<String> keys = manifest.keys();
        while (keys.hasNext()) {
            String key = keys.next();
            boolean known = false;
            for (String expected : MANIFEST_KEYS) {
                if (expected.equals(key)) { known = true; break; }
            }
            if (!known) return false;
        }
        Object code = manifest.opt("versionCode");
        if (!(code instanceof Integer || code instanceof Long)) return false;
        long versionCode = ((Number) code).longValue();
        if (versionCode < 1) return false;
        Object versionName = manifest.opt("versionName");
        Object packageName = manifest.opt("packageName");
        Object assetName = manifest.opt("apkAssetName");
        Object hash = manifest.opt("sha256");
        Object notes = manifest.opt("notes");
        if (!(versionName instanceof String) || ((String) versionName).trim().isEmpty()) return false;
        if (!(packageName instanceof String) || !PACKAGE_NAME.equals(packageName)) return false;
        if (!(assetName instanceof String) || !APK_ASSET.equals(assetName)) return false;
        if (!(hash instanceof String) || !SHA256.matcher((String) hash).matches()) return false;
        return notes instanceof String;
    }

    public static boolean isEligible(long candidateVersionCode, long installedVersionCode,
            String packageName, String expectedPackageName, String apkAssetName,
            String expectedApkAssetName, String sha256, String apkUrl) {
        if (candidateVersionCode <= installedVersionCode) return false;
        if (isBlank(packageName) || !packageName.equals(expectedPackageName)) return false;
        if (isBlank(apkAssetName) || !apkAssetName.equals(expectedApkAssetName)) return false;
        if (isBlank(sha256) || !SHA256.matcher(sha256.toLowerCase(Locale.ROOT)).matches()) return false;
        if (isBlank(apkUrl) ||
                !apkUrl.startsWith("https://github.com/vidift-max/ai-bridge-browser/releases/download/")) return false;
        return true;
    }

    private static boolean isBlank(String value) {
        return value == null || value.trim().isEmpty();
    }
}
