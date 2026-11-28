package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class AgentRosterPolicyTest {
    @Test public void canonicalIdsCoverExactlyTwentyLogicalAgents() {
        assertEquals("AI-01", AgentRosterPolicy.canonicalId(1));
        assertEquals("AI-09", AgentRosterPolicy.canonicalId(9));
        assertEquals("AI-10", AgentRosterPolicy.canonicalId(10));
        assertEquals("AI-20", AgentRosterPolicy.canonicalId(20));
        assertTrue(AgentRosterPolicy.isValidId("AI-01"));
        assertTrue(AgentRosterPolicy.isValidId("AI-20"));
        assertFalse(AgentRosterPolicy.isValidId("AI-00"));
        assertFalse(AgentRosterPolicy.isValidId("AI-21"));
        assertFalse(AgentRosterPolicy.isValidId("AI-1"));
        assertFalse(AgentRosterPolicy.isValidId("ai-01"));
    }

    @Test public void rosterCapacityIsBoundedAndRejectsInvalidCounts() {
        assertTrue(AgentRosterPolicy.canRegister(0));
        assertTrue(AgentRosterPolicy.canRegister(19));
        assertFalse(AgentRosterPolicy.canRegister(20));
        assertFalse(AgentRosterPolicy.canRegister(-1));
    }

    @Test public void providerConcurrencyRemainsTwo() {
        assertEquals(2, AgentRosterPolicy.MAX_CONCURRENT_PROVIDER_SESSIONS);
    }

    @Test public void canonicalIdRejectsOutOfRangeOrdinals() {
        try {
            AgentRosterPolicy.canonicalId(0);
            fail("zero_ordinal_must_fail");
        } catch (IllegalArgumentException expected) {
            assertEquals("agent_ordinal_out_of_range", expected.getMessage());
        }
        try {
            AgentRosterPolicy.canonicalId(21);
            fail("ordinal_above_capacity_must_fail");
        } catch (IllegalArgumentException expected) {
            assertEquals("agent_ordinal_out_of_range", expected.getMessage());
        }
    }
}
