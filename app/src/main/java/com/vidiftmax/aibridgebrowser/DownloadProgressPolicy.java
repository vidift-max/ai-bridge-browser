package com.vidiftmax.aibridgebrowser;

/** Pure progress calculation shared by the updater and JVM tests. */
public final class DownloadProgressPolicy {
    private DownloadProgressPolicy() {}

    public static int percent(long downloadedBytes, long declaredBytes, long maximumBytes) {
        if (downloadedBytes < 0 || declaredBytes <= 0 || maximumBytes <= 0) return -1;
        if (declaredBytes > maximumBytes || downloadedBytes > declaredBytes) return -1;
        return (int) Math.min(100L, (downloadedBytes * 100L) / declaredBytes);
    }
}
