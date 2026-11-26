package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.file.Files;
import org.junit.Test;

public class UpdateInstallPolicyTest {
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
