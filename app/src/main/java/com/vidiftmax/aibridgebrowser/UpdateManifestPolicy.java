package com.vidiftmax.aibridgebrowser;

import java.util.Locale;
import java.util.regex.Pattern;

/** Fail-closed validation for metadata consumed by the in-app updater. */
public final class UpdateManifestPolicy {
    private static final Pattern SHA256 = Pattern.compile("[a-f0-9]{64}");
    private UpdateManifestPolicy() {}

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
