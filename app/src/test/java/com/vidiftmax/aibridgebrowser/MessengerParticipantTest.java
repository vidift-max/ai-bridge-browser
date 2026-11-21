package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class MessengerParticipantTest {
    @Test public void newProfileIsLocalDraftWithoutOfficialIdentity() {
        MessengerParticipant p = new MessengerParticipant("IA de pesquisa", "OpenAI");
        assertTrue(p.getLocalId().startsWith("CONTACT-"));
        assertEquals(MessengerParticipant.State.LOCAL_DRAFT, p.getState());
        assertFalse(p.hasVerifiedRegistryIdentity());
        assertNull(p.getAiId());
        assertNull(p.getPhoneNumber());
        assertNull(p.getSerial());
    }

    @Test public void rejectsMissingOrOversizedFields() {
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerParticipant(" ", "OpenAI"));
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerParticipant("IA", ""));
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerParticipant("x".repeat(81), "OpenAI"));
    }

    @Test public void registryStatesRequireCompleteOfficialIdentity() {
        assertThrows(IllegalArgumentException.class, () ->
                MessengerParticipant.fromLocalRecord("CONTACT-12345678", "IA", "Provider",
                        "ACTIVE", null, null, null));
        MessengerParticipant p = MessengerParticipant.fromLocalRecord(
                "CONTACT-12345678", "IA", "Provider", "DISCONNECTED",
                "AI-ABC-01", "AI-PHONE-002", "AIP-2026-000002");
        assertTrue(p.hasVerifiedRegistryIdentity());
        assertEquals(MessengerParticipant.State.DISCONNECTED, p.getState());
    }

    @Test public void rejectsPartialOfficialIdentity() {
        assertThrows(IllegalArgumentException.class, () ->
                MessengerParticipant.fromLocalRecord("CONTACT-12345678", "IA", "Provider",
                        "PENDING_VERIFICATION", "AI-ABC-01", null, null));
    }
}
