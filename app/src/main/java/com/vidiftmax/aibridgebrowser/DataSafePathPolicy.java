package com.vidiftmax.aibridgebrowser;

import java.nio.charset.StandardCharsets;

/** Rejects archive entry names that could escape a future staging directory. */
public final class DataSafePathPolicy {
    private DataSafePathPolicy() {}

    public static String validate(String path) {
        if (path == null || path.isEmpty()) throw new IllegalArgumentException("path_required");
        if (path.length() > DataSafeLimits.MAX_PATH_UTF8_BYTES
                || path.getBytes(StandardCharsets.UTF_8).length > DataSafeLimits.MAX_PATH_UTF8_BYTES)
            throw new IllegalArgumentException("path_too_long");
        if (path.startsWith("/") || path.startsWith("\\") || path.indexOf('\\') >= 0
                || path.indexOf(':') >= 0 || path.indexOf('\0') >= 0)
            throw new IllegalArgumentException("path_absolute_or_invalid");
        String[] segments = path.split("/", -1);
        for (String segment : segments) {
            if (segment.isEmpty() || ".".equals(segment) || "..".equals(segment))
                throw new IllegalArgumentException("path_segment_invalid");
            for (int i = 0; i < segment.length(); i++) {
                char c = segment.charAt(i);
                if (c < 0x20 || c == 0x7f) throw new IllegalArgumentException("path_control_character");
            }
        }
        return path;
    }
}
