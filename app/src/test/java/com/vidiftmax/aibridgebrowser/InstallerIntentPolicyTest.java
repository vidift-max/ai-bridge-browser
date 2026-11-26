package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import android.content.Intent;

import org.junit.Test;

public class InstallerIntentPolicyTest {
    private static final String AUTHORITY = "com.vidiftmax.aibridgebrowser.fileprovider";
    private static final String MIME = "application/vnd.android.package-archive";
    private static final String APK_URI =
            "content://" + AUTHORITY + "/app_update_apk/app-release.apk";
    private static final int READ_ONLY_FLAGS =
            Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK;

    @Test public void acceptsOnlyCanonicalProviderApkUri() {
        assertTrue(InstallerIntentPolicy.isSafeHandoff(
                APK_URI, AUTHORITY, MIME, READ_ONLY_FLAGS));
    }

    @Test public void rejectsWrongSchemeAuthorityAndProviderConfusion() {
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                "file:///data/local/tmp/app-release.apk", AUTHORITY, MIME, READ_ONLY_FLAGS));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                "content://attacker.provider/app_update_apk/app-release.apk",
                AUTHORITY, MIME, READ_ONLY_FLAGS));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                "content://" + AUTHORITY + ".attacker/app_update_apk/app-release.apk",
                AUTHORITY, MIME, READ_ONLY_FLAGS));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                "content://user@" + AUTHORITY + "/app_update_apk/app-release.apk",
                AUTHORITY, MIME, READ_ONLY_FLAGS));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                "content://" + AUTHORITY + ":443/app_update_apk/app-release.apk",
                AUTHORITY, MIME, READ_ONLY_FLAGS));
    }

    @Test public void rejectsPathTraversalAndNonCanonicalPath() {
        String[] invalidUris = {
            "content://" + AUTHORITY + "/app_update_apk/../app-release.apk",
            "content://" + AUTHORITY + "/app_update_apk/%2e%2e/app-release.apk",
            "content://" + AUTHORITY + "/app_update_apk/%2Fapp-release.apk",
            "content://" + AUTHORITY + "/app_update_apk//app-release.apk",
            "content://" + AUTHORITY + "/other/app-release.apk",
            "content://" + AUTHORITY + "/app_update_apk/app-debug.apk",
            "content://" + AUTHORITY + "/app_update_apk/app-release.apk/extra"
        };
        for (String uri : invalidUris) {
            assertFalse("Unexpectedly accepted: " + uri,
                    InstallerIntentPolicy.isSafeHandoff(uri, AUTHORITY, MIME, READ_ONLY_FLAGS));
        }
    }

    @Test public void rejectsQueryFragmentAndMalformedUri() {
        String[] invalidUris = {
            APK_URI + "?redirect=elsewhere",
            APK_URI + "#fragment",
            APK_URI + "\\evil",
            "content://[" + AUTHORITY + "/app_update_apk/app-release.apk",
            " content://" + AUTHORITY + "/app_update_apk/app-release.apk"
        };
        for (String uri : invalidUris) {
            assertFalse("Unexpectedly accepted: " + uri,
                    InstallerIntentPolicy.isSafeHandoff(uri, AUTHORITY, MIME, READ_ONLY_FLAGS));
        }
    }

    @Test public void rejectsWrongMimeAndUnexpectedFlags() {
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                APK_URI, AUTHORITY, "application/octet-stream", READ_ONLY_FLAGS));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                APK_URI, AUTHORITY, MIME, Intent.FLAG_GRANT_WRITE_URI_PERMISSION));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(APK_URI, AUTHORITY, MIME, 0));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                APK_URI, AUTHORITY, MIME,
                READ_ONLY_FLAGS | Intent.FLAG_GRANT_WRITE_URI_PERMISSION));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                APK_URI, AUTHORITY, MIME, READ_ONLY_FLAGS | Intent.FLAG_ACTIVITY_CLEAR_TASK));
    }

    @Test public void rejectsMissingOrInvalidAuthorityAndNullInputs() {
        assertFalse(InstallerIntentPolicy.isSafeHandoff(null, AUTHORITY, MIME, READ_ONLY_FLAGS));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(APK_URI, null, MIME, READ_ONLY_FLAGS));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(APK_URI, " ", MIME, READ_ONLY_FLAGS));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(APK_URI, AUTHORITY, null, READ_ONLY_FLAGS));
    }
}
