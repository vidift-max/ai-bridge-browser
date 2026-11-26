package com.vidiftmax.aibridgebrowser;

import android.content.Intent;

/** Strict allowlist for the URI and permissions handed to Android's package installer. */
public final class InstallerIntentPolicy {
    private static final String APK_MIME = "application/vnd.android.package-archive";
    private InstallerIntentPolicy() {}

    public static boolean isSafeHandoff(String uri, String expectedAuthority,
            String mimeType, int flags) {
        if (uri == null || expectedAuthority == null || expectedAuthority.trim().isEmpty()
                || !APK_MIME.equals(mimeType)) return false;
        String prefix = "content://" + expectedAuthority + "/";
        if (!uri.startsWith(prefix) || uri.length() <= prefix.length()
                || uri.indexOf('?') >= 0 || uri.indexOf('#') >= 0
                || uri.indexOf('\\') >= 0) return false;
        int read = flags & Intent.FLAG_GRANT_READ_URI_PERMISSION;
        int write = flags & Intent.FLAG_GRANT_WRITE_URI_PERMISSION;
        return read != 0 && write == 0;
    }
}
