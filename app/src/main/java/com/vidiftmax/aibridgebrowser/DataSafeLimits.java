package com.vidiftmax.aibridgebrowser;

/** Central defensive limits for future DATA SAFE archive readers and writers. */
public final class DataSafeLimits {
    public static final int MAX_ARCHIVE_BYTES = 256 * 1024 * 1024;
    public static final int MAX_ENTRIES = 4096;
    public static final long MAX_ENTRY_BYTES = 32L * 1024 * 1024;
    public static final long MAX_TOTAL_EXPANDED_BYTES = 256L * 1024 * 1024;
    public static final int MAX_PATH_UTF8_BYTES = 1024;
    public static final int MAX_COMPRESSION_RATIO = 100;

    private DataSafeLimits() {}
}
