package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import org.junit.Test;

public class UpdaterDownloadPolicyTest {
    @Test public void acceptsExactDeclaredLength() {
        assertTrue(UpdaterDownloadPolicy.isValidLength(1024, 1024, 2048));
    }
    @Test public void acceptsUnknownLengthWithinLimit() {
        assertTrue(UpdaterDownloadPolicy.isValidLength(-1, 1024, 2048));
    }
    @Test public void rejectsTruncatedOrOverlongDownload() {
        assertFalse(UpdaterDownloadPolicy.isValidLength(1024, 1023, 2048));
        assertFalse(UpdaterDownloadPolicy.isValidLength(1024, 1025, 2048));
    }
    @Test public void rejectsNegativeOrOversizedActualLength() {
        assertFalse(UpdaterDownloadPolicy.isValidLength(-1, -1, 2048));
        assertFalse(UpdaterDownloadPolicy.isValidLength(-1, 2049, 2048));
        assertFalse(UpdaterDownloadPolicy.isValidLength(-2, 1024, 2048));
    }
    @Test public void bindsActualLengthToReleaseAssetMetadata() {
        assertTrue(UpdaterDownloadPolicy.isExpectedAssetLength(2048, 2048, 2048, 4096));
        assertTrue(UpdaterDownloadPolicy.isExpectedAssetLength(-1, 2048, 2048, 4096));
    }
    @Test public void rejectsContentLengthMismatchAgainstReleaseMetadata() {
        assertFalse(UpdaterDownloadPolicy.isExpectedAssetLength(2047, 2048, 2048, 4096));
        assertFalse(UpdaterDownloadPolicy.isExpectedAssetLength(2049, 2048, 2048, 4096));
        assertFalse(UpdaterDownloadPolicy.isExpectedAssetLength(-1, 2047, 2048, 4096));
        assertFalse(UpdaterDownloadPolicy.isExpectedAssetLength(-1, 2049, 2048, 4096));
    }
    @Test public void rejectsInvalidExpectedAssetSizes() {
        assertFalse(UpdaterDownloadPolicy.isExpectedAssetLength(0, 0, 0, 4096));
        assertFalse(UpdaterDownloadPolicy.isExpectedAssetLength(4097, 4097, 4097, 4096));
        assertFalse(UpdaterDownloadPolicy.isExpectedAssetLength(-1, 1024, 2048, 1023));
    }
}
