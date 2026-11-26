package com.vidiftmax.aibridgebrowser;

/** Pure validation for completed updater downloads. */
public final class UpdaterDownloadPolicy {
    private UpdaterDownloadPolicy() {}

    public static boolean isValidLength(long declaredBytes, long actualBytes, long maximumBytes) {
        return actualBytes >= 0 && maximumBytes >= 0 && actualBytes <= maximumBytes
                && (declaredBytes < 0 || declaredBytes == actualBytes);
    }
}
