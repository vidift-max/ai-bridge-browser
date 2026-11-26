package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import android.content.Intent;

import org.junit.Test;

public class InstallerIntentPolicyTest {
    private static final String AUTHORITY = "com.vidiftmax.aibridgebrowser.fileprovider";
    private static final String MIME = "application/vnd.android.package-archive";

    @Test public void acceptsOnlyContentUriWithReadGrant() {
        assertTrue(InstallerIntentPolicy.isSafeHandoff(
                "content://" + AUTHORITY + "/app_update_apk/app-release.apk",
                AUTHORITY, MIME, Intent.FLAG_GRANT_READ_URI_PERMISSION));
    }

    @Test public void rejectsFileUriAndForeignAuthority() {
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                "file:///data/local/tmp/app.apk", AUTHORITY, MIME,
                Intent.FLAG_GRANT_READ_URI_PERMISSION));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                "content://attacker.provider/app.apk", AUTHORITY, MIME,
                Intent.FLAG_GRANT_READ_URI_PERMISSION));
    }

    @Test public void rejectsWriteGrantAndMissingReadGrant() {
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                "content://" + AUTHORITY + "/app_update_apk/app-release.apk",
                AUTHORITY, MIME, Intent.FLAG_GRANT_WRITE_URI_PERMISSION));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                "content://" + AUTHORITY + "/app_update_apk/app-release.apk",
                AUTHORITY, MIME, 0));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                "content://" + AUTHORITY + "/app_update_apk/app-release.apk",
                AUTHORITY, MIME,
                Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION));
    }

    @Test public void rejectsWrongMimeAndUriSuffixInjection() {
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                "content://" + AUTHORITY + "/app.apk", AUTHORITY,
                "application/octet-stream", Intent.FLAG_GRANT_READ_URI_PERMISSION));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                "content://" + AUTHORITY + "/app.apk?redirect=elsewhere", AUTHORITY,
                MIME, Intent.FLAG_GRANT_READ_URI_PERMISSION));
        assertFalse(InstallerIntentPolicy.isSafeHandoff(
                "content://" + AUTHORITY + "/app.apk#fragment", AUTHORITY,
                MIME, Intent.FLAG_GRANT_READ_URI_PERMISSION));
    }
}
