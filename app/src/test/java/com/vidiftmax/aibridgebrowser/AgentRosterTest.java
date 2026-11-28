package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class AgentRosterTest {
    @Test public void registersTwentyLogicalAgentsButOnlyTwoCanBeBusy() {
        AgentRoster roster = new AgentRoster();
        for (int i = 1; i <= 20; i++) {
            String id = AgentRosterPolicy.canonicalId(i);
            assertTrue(roster.register(id, "Agent " + i, "specialty-" + i));
        }
        assertEquals(20, roster.size());
        assertFalse(roster.register("AI-21", "Extra", "none"));
        assertTrue(roster.setStatus("AI-01", AgentRoster.Status.BUSY));
        assertTrue(roster.setStatus("AI-02", AgentRoster.Status.BUSY));
        assertFalse(roster.setStatus("AI-03", AgentRoster.Status.BUSY));
        assertEquals(2, roster.busyCount());
    }

    @Test public void rejectsDuplicatesAndInvalidIds() {
        AgentRoster roster = new AgentRoster();
        assertTrue(roster.register("AI-01", "Primary", "coordination"));
        assertFalse(roster.register("AI-01", "Duplicate", "other"));
        assertFalse(roster.register("AI-00", "Invalid", "other"));
        assertFalse(roster.register("AI-02", " ", "other"));
    }

    @Test public void cannotRemoveBusyAgent() {
        AgentRoster roster = new AgentRoster();
        assertTrue(roster.register("AI-01", "Primary", "coordination"));
        assertTrue(roster.setStatus("AI-01", AgentRoster.Status.BUSY));
        assertFalse(roster.remove("AI-01"));
        assertTrue(roster.setStatus("AI-01", AgentRoster.Status.PAUSED));
        assertTrue(roster.remove("AI-01"));
    }
}
