package com.vidiftmax.aibridgebrowser;

import android.content.Intent;

import java.net.URI;
import java.net.URISyntaxException;

/** Strict allowlist for the URI and permissions handed to Android's package installer. */
public final class InstallerIntentPolicy {
    private static final String APK_MIME = "application/vnd.android.package-archive";
    private static final String APK_PATH = "/app_update_apk/app-release.apk";
    private static final int ALLOWED_FLAGS =
            Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK;

    private InstallerIntentPolicy() {}

    public static boolean isSafeHandoff(String uri, String expectedAuthority,
            String mimeType, int flags) {
        if (uri == null || expectedAuthority == null || expectedAuthority.trim().isEmpty()
                || !APK_MIME.equals(mimeType) || (flags & ~ALLOWED_FLAGS) != 0) {
            return false;
        }
        try {
            URI parsed = new URI(uri);
            return "content".equals(parsed.getScheme())
                    && expectedAuthority.equals(parsed.getRawAuthority())
                    && expectedAuthority.equals(parsed.getHost())
                    && parsed.getRawUserInfo() == null
                    && parsed.getPort() == -1
                    && APK_PATH.equals(parsed.getRawPath())
                    && parsed.getRawQuery() == null
                    && parsed.getRawFragment() == null
                    && uri.equals(parsed.toASCIIString())
                    && (flags & Intent.FLAG_GRANT_READ_URI_PERMISSION) != 0
                    && (flags & Intent.FLAG_GRANT_WRITE_URI_PERMISSION) == 0;
        } catch (URISyntaxException invalidUri) {
            return false;
        }
    }
}
