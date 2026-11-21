package com.vidiftmax.aibridgebrowser;

public final class MessengerIdempotency {
    private MessengerIdempotency() {}

    public static boolean isValidKey(String key) {
        return key != null && !key.trim().isEmpty() && key.length() <= 200;
    }

    public static boolean matches(String storedPayloadFingerprint, String incomingPayloadFingerprint) {
        return storedPayloadFingerprint != null
                && incomingPayloadFingerprint != null
                && storedPayloadFingerprint.equals(incomingPayloadFingerprint);
    }
}
