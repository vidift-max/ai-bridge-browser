package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public final class MessengerLocalStateTest {
    @Test public void acceptsOnlyLocalStates() {
        assertTrue(MessengerLocalState.isValid(MessengerLocalState.SAVED_LOCAL));
        assertTrue(MessengerLocalState.isValid(MessengerLocalState.READ_LOCAL));
        assertTrue(MessengerLocalState.isValid(MessengerLocalState.ARCHIVED_LOCAL));
    }

    @Test public void rejectsRemoteDeliveryStates() {
        assertFalse(MessengerLocalState.isValid("SENT"));
        assertFalse(MessengerLocalState.isValid("DELIVERED"));
        assertFalse(MessengerLocalState.isValid("ACKNOWLEDGED"));
    }
}
