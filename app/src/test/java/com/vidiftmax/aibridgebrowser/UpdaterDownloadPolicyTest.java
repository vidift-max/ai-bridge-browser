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
}
