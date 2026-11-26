package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.file.Files;
import org.junit.Test;

public class UpdateInstallPolicyTest {
    @Test public void requiresSamePackageAndSigningCertificateToPreserveInstallIdentity() {
        assertTrue(UpdateInstallPolicy.isSameApplicationIdentity("com.example.app", "com.example.app", true));
        assertFalse(UpdateInstallPolicy.isSameApplicationIdentity("com.example.app", "com.other.app", true));
        assertFalse(UpdateInstallPolicy.isSameApplicationIdentity("com.example.app", "com.example.app", false));
        assertFalse(UpdateInstallPolicy.isSameApplicationIdentity(null, "com.example.app", true));
    }

    @Test public void acceptsOnlyVerifiedApkInPrivateUpdateDirectory() throws Exception {
        File root = Files.createTempDirectory("updater-policy").toFile();
        File updates = new File(root, "updates");
        assertTrue(updates.mkdir());
        File apk = new File(updates, "app-release.apk");
        try (FileOutputStream output = new FileOutputStream(apk)) { output.write(new byte[]{1,2,3}); }
        assertTrue(UpdateInstallPolicy.isEligibleCandidate(apk, apk, updates, "app-release.apk"));
    }

    @Test public void rejectsOutsideFileWrongNameAndDifferentVerifiedFile() throws Exception {
        File root = Files.createTempDirectory("updater-policy").toFile();
        File updates = new File(root, "updates");
        assertTrue(updates.mkdir());
        File outside = new File(root, "app-release.apk");
        try (FileOutputStream output = new FileOutputStream(outside)) { output.write(1); }
        File insideWrongName = new File(updates, "other.apk");
        try (FileOutputStream output = new FileOutputStream(insideWrongName)) { output.write(1); }
        File expected = new File(updates, "app-release.apk");
        assertFalse(UpdateInstallPolicy.isEligibleCandidate(outside, outside, updates, "app-release.apk"));
        assertFalse(UpdateInstallPolicy.isEligibleCandidate(insideWrongName, insideWrongName, updates, "app-release.apk"));
        assertFalse(UpdateInstallPolicy.isEligibleCandidate(insideWrongName, expected, updates, "other.apk"));
    }

    @Test public void rejectsMissingAndEmptyFiles() throws Exception {
        File root = Files.createTempDirectory("updater-policy").toFile();
        File updates = new File(root, "updates");
        assertTrue(updates.mkdir());
        File empty = new File(updates, "app-release.apk");
        assertTrue(empty.createNewFile());
        assertFalse(UpdateInstallPolicy.isEligibleCandidate(empty, empty, updates, "app-release.apk"));
        assertFalse(UpdateInstallPolicy.isEligibleCandidate(new File(updates, "missing.apk"),
                new File(updates, "missing.apk"), updates, "missing.apk"));
    }
}

    @Test public void requiresExactOfficialAssetLengthBeforeInstallerHandoff() throws Exception {
        File root = Files.createTempDirectory("updater-size").toFile();
        File updates = new File(root, "updates");
        assertTrue(updates.mkdir());
        File apk = new File(updates, "app-release.apk");
        try (FileOutputStream output = new FileOutputStream(apk)) { output.write(new byte[]{1,2,3,4}); }
        assertTrue(UpdateInstallPolicy.isExpectedVerifiedApk(
                apk, apk, updates, "app-release.apk", 4, 1024));
        assertFalse(UpdateInstallPolicy.isExpectedVerifiedApk(
                apk, apk, updates, "app-release.apk", 5, 1024));
        assertFalse(UpdateInstallPolicy.isExpectedVerifiedApk(
                apk, apk, updates, "app-release.apk", 3, 1024));
    }

    @Test public void rejectsInvalidOrOversizedExpectedAssetLengthAtInstallTime() throws Exception {
        File root = Files.createTempDirectory("updater-size").toFile();
        File updates = new File(root, "updates");
        assertTrue(updates.mkdir());
        File apk = new File(updates, "app-release.apk");
        try (FileOutputStream output = new FileOutputStream(apk)) { output.write(new byte[]{1,2,3,4}); }
        assertFalse(UpdateInstallPolicy.isExpectedVerifiedApk(
                apk, apk, updates, "app-release.apk", 0, 1024));
        assertFalse(UpdateInstallPolicy.isExpectedVerifiedApk(
                apk, apk, updates, "app-release.apk", 4, 3));
        assertFalse(UpdateInstallPolicy.isExpectedVerifiedApk(
                apk, apk, updates, "app-release.apk", 4, 0));
    }

    @Test public void sizeGateStillRequiresTheExactVerifiedFileAndPrivatePath() throws Exception {
        File root = Files.createTempDirectory("updater-size").toFile();
        File updates = new File(root, "updates");
        assertTrue(updates.mkdir());
        File apk = new File(updates, "app-release.apk");
        File other = new File(updates, "other.apk");
        try (FileOutputStream output = new FileOutputStream(apk)) { output.write(new byte[]{1,2,3,4}); }
        try (FileOutputStream output = new FileOutputStream(other)) { output.write(new byte[]{1,2,3,4}); }
        assertFalse(UpdateInstallPolicy.isExpectedVerifiedApk(
                apk, other, updates, "app-release.apk", 4, 1024));
        assertFalse(UpdateInstallPolicy.isExpectedVerifiedApk(
                other, other, updates, "app-release.apk", 4, 1024));
    }
}
