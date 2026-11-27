package com.vidiftmax.aibridgebrowser;

/** Pure validation for completed updater downloads. */
public final class UpdaterDownloadPolicy {
    private UpdaterDownloadPolicy() {}

    public static boolean isValidLength(long declaredBytes, long actualBytes, long maximumBytes) {
        return declaredBytes >= -1 && actualBytes >= 0 && maximumBytes >= 0 && actualBytes <= maximumBytes
                && (declaredBytes == -1 || declaredBytes == actualBytes);
    }

    /** Enforces the byte count advertised by the official Release asset metadata. */
    public static boolean isExpectedAssetLength(long declaredBytes, long actualBytes,
            long expectedBytes, long maximumBytes) {
        return expectedBytes > 0 && expectedBytes <= maximumBytes
                && (declaredBytes == -1 || declaredBytes == expectedBytes)
                && actualBytes == expectedBytes
                && isValidLength(declaredBytes, actualBytes, maximumBytes);
    }
}
