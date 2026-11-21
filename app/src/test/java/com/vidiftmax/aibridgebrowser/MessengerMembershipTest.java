package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class MessengerMembershipTest {
    @Test public void createsLocalSelectionOnly() {
        MessengerMembership m = new MessengerMembership("LOCAL-DEMO", "CONTACT-12345678");
        assertEquals("LOCAL-DEMO", m.getConversationId());
        assertEquals("CONTACT-12345678", m.getParticipantLocalId());
        assertEquals(MessengerMembership.State.LOCAL_SELECTED, m.getState());
    }

    @Test public void rejectsInvalidMembershipKeys() {
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerMembership("", "CONTACT-12345678"));
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerMembership("LOCAL-DEMO", "bad"));
    }
}
