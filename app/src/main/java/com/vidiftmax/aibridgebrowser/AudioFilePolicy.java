package com.vidiftmax.aibridgebrowser;

public final class AudioFilePolicy {
    public static final long MAX_BYTES = 5L * 1024L * 1024L;

    private AudioFilePolicy() {}

    public static void validateSize(long bytes) {
        if (bytes <= 0 || bytes > MAX_BYTES) throw new IllegalArgumentException("invalid_audio_size");
    }

    public static String contentTypeForRecording() {
        return "audio/mp4";
    }
}
