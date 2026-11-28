package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class AgentCoordinatorTest {
    @Test public void gpt6CoordinatesOnlyRegisteredAgentsAndCurrentProviderPair() {
        AgentCoordinator coordinator = new AgentCoordinator();
        assertEquals("GPT-6", coordinator.coordinatorId());
        assertTrue(coordinator.registerAgent("AI-01", "Primary", "implementation"));
        assertTrue(coordinator.registerAgent("AI-02", "Secondary", "verification"));
        assertTrue(coordinator.registerAgent("AI-03", "Future", "queued-only"));
        assertFalse(coordinator.assignMission("unknown", "AI-04", "not registered"));
        assertTrue(coordinator.assignMission("m3", "AI-03", "wait for future phase"));
        assertTrue(coordinator.assignMission("m1", "AI-01", "implement"));
        assertTrue(coordinator.assignMission("m2", "AI-02", "review"));

        assertEquals("m1", coordinator.dispatchNext().missionId);
        assertEquals("m2", coordinator.dispatchNext().missionId);
        assertNull(coordinator.dispatchNext());
        assertEquals(2, coordinator.activeProviderSessions());
        assertEquals(AgentRoster.Status.BUSY, coordinator.agent("AI-01").status);
        assertTrue(coordinator.completeMission("m1"));
        assertEquals(AgentRoster.Status.READY, coordinator.agent("AI-01").status);
        assertTrue(coordinator.completeMission("m2"));
        assertNull(coordinator.dispatchNext());
    }

    @Test public void coordinatorCannotActivateOutOfScopeAgent() {
        AgentCoordinator coordinator = new AgentCoordinator();
        assertTrue(coordinator.registerAgent("AI-03", "Future", "queued"));
        assertTrue(coordinator.assignMission("m3", "AI-03", "not active this phase"));
        assertNull(coordinator.dispatchNext());
        assertEquals(0, coordinator.activeProviderSessions());
    }
}
