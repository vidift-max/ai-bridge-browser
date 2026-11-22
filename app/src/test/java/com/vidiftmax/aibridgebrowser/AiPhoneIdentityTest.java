package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class AiPhoneIdentityTest {
    @Test public void unassignedIdentityDoesNotInventOfficialIdentifiers() {
        AiPhoneIdentity identity = AiPhoneIdentity.unassigned();
        assertFalse(identity.isRegistryAssigned());
        assertNull(identity.getAiId());
        assertNull(identity.getDisplayNumber());
        assertNull(identity.getSerial());
        assertEquals(AiPhoneIdentity.Status.INVITED, identity.getStatus());
    }

    @Test public void acceptsServerFormatRegistryRecord() {
        AiPhoneIdentity identity = AiPhoneIdentity.fromRegistryRecord(
                "AI-PARTICIPANT-02", "Participante 02", "configured", "ACTIVE",
                "AI-PHONE-000002", "AIP-2026-00000002");
        assertTrue(identity.isRegistryAssigned());
        assertEquals("AI-PHONE-000002", identity.getDisplayNumber());
        assertEquals("AIP-2026-00000002", identity.getSerial());
        assertEquals(AiPhoneIdentity.Status.ACTIVE, identity.getStatus());
    }

    @Test public void rejectsMalformedOrMissingRegistryIdentifiers() {
        assertThrows(IllegalArgumentException.class, () ->
                AiPhoneIdentity.fromRegistryRecord(" ", "Nome", "provider", "ACTIVE",
                        "AI-PHONE-000002", "AIP-2026-00000002"));
        assertThrows(IllegalArgumentException.class, () ->
                AiPhoneIdentity.fromRegistryRecord("AI-02", "Nome", "provider", "ACTIVE",
                        "AI-PHONE-02", "AIP-2026-00000002"));
        assertThrows(IllegalArgumentException.class, () ->
                AiPhoneIdentity.fromRegistryRecord("AI-02", "Nome", "provider", "UNKNOWN",
                        "AI-PHONE-000002", "AIP-2026-00000002"));
    }

    @Test public void rejectsNumbersShorterThanServerAllocationFormat() {
        assertThrows(IllegalArgumentException.class, () ->
                AiPhoneIdentity.fromRegistryRecord("AI-02", "Nome", "configured", "ACTIVE",
                        "AI-PHONE-002", "AIP-2026-00000002"));
    }
}
