package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class MessengerInvitationDraftTest {
    @Test public void createsLocalOnlyInvitationDraft() {
        MessengerInvitationDraft d = new MessengerInvitationDraft(
                "CONTACT-12345678", "Convite de participação no projeto AI-PHONE.");
        assertTrue(d.getInvitationId().startsWith("INVITE-LOCAL-"));
        assertEquals(MessengerInvitationDraft.STATUS_LOCAL_DRAFT, d.getStatus());
        assertEquals("CONTACT-12345678", d.getParticipantLocalId());
    }

    @Test public void rejectsInvalidDraft() {
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerInvitationDraft("bad", "Convite"));
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerInvitationDraft("CONTACT-12345678", " "));
    }
}
