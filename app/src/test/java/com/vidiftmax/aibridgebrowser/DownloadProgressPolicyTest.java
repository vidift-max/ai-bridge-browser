package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertEquals;
import org.junit.Test;

public class DownloadProgressPolicyTest {
    @Test public void calculatesProgressFromKnownContentLength() {
        assertEquals(0, DownloadProgressPolicy.percent(0, 1000, 2000));
        assertEquals(25, DownloadProgressPolicy.percent(250, 1000, 2000));
        assertEquals(100, DownloadProgressPolicy.percent(1000, 1000, 2000));
    }

    @Test public void rejectsUnknownOrInvalidLengths() {
        assertEquals(-1, DownloadProgressPolicy.percent(10, -1, 2000));
        assertEquals(-1, DownloadProgressPolicy.percent(-1, 100, 2000));
        assertEquals(-1, DownloadProgressPolicy.percent(101, 100, 2000));
        assertEquals(-1, DownloadProgressPolicy.percent(1, 3000, 2000));
    }
}
