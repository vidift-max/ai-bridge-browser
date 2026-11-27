package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class AgentRosterPolicyTest {
    @Test public void canonicalIdsCoverExactlyTwentyLogicalAgents() {
        assertEquals("AI-01", AgentRosterPolicy.canonicalId(1));
        assertEquals("AI-09", AgentRosterPolicy.canonicalId(9));
        assertEquals("AI-10", AgentRosterPolicy.canonicalId(10));
        assertEquals("AI-20", AgentRosterPolicy.canonicalId(20));
        assertThrows(IllegalArgumentException.class,
                () -> AgentRosterPolicy.canonicalId(0));
        assertThrows(IllegalArgumentException.class,
                () -> AgentRosterPolicy.canonicalId(21));
    }

    @Test public void identityValidationRejectsAliasesAndOutOfRangeIds() {
        for (int i = 1; i <= 20; i++) {
            assertTrue(AgentRosterPolicy.isValidId(AgentRosterPolicy.canonicalId(i)));
        }
        assertFalse(AgentRosterPolicy.isValidId("AI-00"));
        assertFalse(AgentRosterPolicy.isValidId("AI-21"));
        assertFalse(AgentRosterPolicy.isValidId("AI-1"));
        assertFalse(AgentRosterPolicy.isValidId("ai-01"));
        assertFalse(AgentRosterPolicy.isValidId("AI-01 "));
        assertFalse(AgentRosterPolicy.isValidId(null));
    }

    @Test public void rosterCapacityDoesNotImplyTwentyConcurrentProviderSessions() {
        assertTrue(AgentRosterPolicy.canRegister(0));
        assertTrue(AgentRosterPolicy.canRegister(19));
        assertFalse(AgentRosterPolicy.canRegister(20));
        assertFalse(AgentRosterPolicy.canRegister(-1));

        assertTrue(AgentRosterPolicy.canOpenProviderSession(0));
        assertTrue(AgentRosterPolicy.canOpenProviderSession(1));
        assertFalse(AgentRosterPolicy.canOpenProviderSession(2));
        assertFalse(AgentRosterPolicy.canOpenProviderSession(20));
        assertFalse(AgentRosterPolicy.canOpenProviderSession(-1));
    }

    @Test public void currentProviderSessionScopeRemainsAi01AndAi02() {
        assertTrue(AgentRosterPolicy.isProviderSessionAllowedForCurrentMission("AI-01"));
        assertTrue(AgentRosterPolicy.isProviderSessionAllowedForCurrentMission("AI-02"));
        assertFalse(AgentRosterPolicy.isProviderSessionAllowedForCurrentMission("AI-03"));
        assertFalse(AgentRosterPolicy.isProviderSessionAllowedForCurrentMission("AI-20"));
    }
}
