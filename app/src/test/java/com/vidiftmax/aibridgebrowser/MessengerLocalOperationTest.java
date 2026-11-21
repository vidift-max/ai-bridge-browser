package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;

public final class MessengerLocalOperationTest {
    @Test public void createsUniqueLocalOperation() {
        MessengerLocalOperation a = new MessengerLocalOperation("msg-1", "SAVE_LOCAL", 1700000000000L);
        MessengerLocalOperation b = new MessengerLocalOperation("msg-1", "SAVE_LOCAL", 1700000000000L);
        assertNotEquals(a.getOperationId(), b.getOperationId());
        assertEquals("msg-1", a.getMessageId());
        assertEquals("SAVE_LOCAL", a.getOperation());
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsMissingMessage() {
        new MessengerLocalOperation("", "SAVE_LOCAL", 1700000000000L);
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsInvalidTimestamp() {
        new MessengerLocalOperation("msg-1", "SAVE_LOCAL", 0);
    }
}
