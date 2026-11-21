package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class MessengerIdempotencyTest {
    @Test public void validatesNonBlankBoundedKey() {
        assertTrue(MessengerIdempotency.isValidKey("req-123"));
        assertFalse(MessengerIdempotency.isValidKey(""));
        assertFalse(MessengerIdempotency.isValidKey(null));
    }

    @Test public void sameFingerprintMatches() {
        assertTrue(MessengerIdempotency.matches("abc", "abc"));
        assertFalse(MessengerIdempotency.matches("abc", "def"));
    }
}
