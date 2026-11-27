package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class AgentRosterTest {
    @Test public void registersTwentyUniqueLogicalAgentsWithoutCreatingSessions() {
        AgentRoster roster = new AgentRoster();
        for (int i = 1; i <= 20; i++) {
            String id = AgentRosterPolicy.canonicalId(i);
            assertTrue(roster.register(id, "Agent " + i, "Specialty " + i));
        }
        assertEquals(20, roster.all().size());
        assertEquals(AgentRoster.Status.OFFLINE, roster.find("AI-01").status);
        assertFalse(roster.register("AI-21", "Agent 21", "Extra"));
    }

    @Test public void rejectsDuplicateMalformedAndIncompleteIdentity() {
        AgentRoster roster = new AgentRoster();
        assertTrue(roster.register("AI-01", "Coordinator", "Coordination"));
        assertFalse(roster.register("AI-01", "Duplicate", "Other"));
        assertFalse(roster.register("AI-02", " ", "SEO"));
        assertFalse(roster.register("bad-id", "Agent", "SEO"));
        assertFalse(roster.register(null, "Agent", "SEO"));
        assertEquals(1, roster.all().size());
    }

    @Test public void statusAndRemovalAreScopedToExactAgent() {
        AgentRoster roster = new AgentRoster();
        assertTrue(roster.register("AI-01", "One", "Coordination"));
        assertTrue(roster.register("AI-02", "Two", "Research"));
        assertTrue(roster.setStatus("AI-02", AgentRoster.Status.BUSY));
        assertEquals(AgentRoster.Status.OFFLINE, roster.find("AI-01").status);
        assertEquals(AgentRoster.Status.BUSY, roster.find("AI-02").status);
        assertFalse(roster.setStatus("AI-03", AgentRoster.Status.READY));
        assertTrue(roster.remove("AI-01"));
        assertNull(roster.find("AI-01"));
        assertEquals(1, roster.all().size());
    }

    @Test public void exposedRosterCannotBeMutatedByCallers() {
        AgentRoster roster = new AgentRoster();
        assertTrue(roster.register("AI-01", "One", "Coordination"));
        try {
            roster.all().clear();
            fail("roster_view_must_be_unmodifiable");
        } catch (UnsupportedOperationException expected) {
            assertEquals(1, roster.all().size());
        }
    }
}
