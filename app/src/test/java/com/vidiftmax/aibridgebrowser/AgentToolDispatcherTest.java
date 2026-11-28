package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.json.JSONObject;
import org.junit.Test;

public class AgentToolDispatcherTest {
    @Test public void dispatchesOnlyFromRunningAi01OrAi02Mission() throws Exception {
        AgentCoordinator coordinator = new AgentCoordinator();
        assertTrue(coordinator.registerAgent("AI-01", "Primary", "implementation"));
        assertTrue(coordinator.registerAgent("AI-02", "Secondary", "verification"));
        assertTrue(coordinator.assignMission("m1", "AI-01", "use a local tool"));
        assertEquals("m1", coordinator.dispatchNext().missionId);

        AgentToolDispatcher dispatcher = new AgentToolDispatcher(coordinator);
        final String[] seen = new String[2];
        assertTrue(dispatcher.bindInvoker("AI-01", (toolId, version, input) -> {
            seen[0] = toolId;
            seen[1] = version;
            return new JSONObject().put("ok", true);
        }));

        JSONObject result = dispatcher.dispatch("m1", "duration_timer", "1.0.0",
                new JSONObject().put("duration", "2m"));
        assertTrue(result.getBoolean("ok"));
        assertEquals("duration_timer", seen[0]);
        assertEquals("1.0.0", seen[1]);
    }

    @Test public void refusesUnboundAgentUnknownToolAndNonCanonicalVersion() throws Exception {
        AgentCoordinator coordinator = new AgentCoordinator();
        assertTrue(coordinator.registerAgent("AI-02", "Secondary", "verification"));
        assertTrue(coordinator.assignMission("m2", "AI-02", "tool"));
        assertEquals("m2", coordinator.dispatchNext().missionId);
        AgentToolDispatcher dispatcher = new AgentToolDispatcher(coordinator);

        assertThrows(IllegalStateException.class,
                () -> dispatcher.dispatch("m2", "duration_timer", "1.0.0", new JSONObject()));
        assertTrue(dispatcher.bindInvoker("AI-02", (tool, version, input) -> new JSONObject()));
        assertThrows(IllegalArgumentException.class,
                () -> dispatcher.dispatch("m2", "unknown", "1.0.0", new JSONObject()));
        assertThrows(IllegalArgumentException.class,
                () -> dispatcher.dispatch("m2", "duration_timer", "1.0", new JSONObject()));
    }

    @Test public void futureAiCannotBindOrDispatch() {
        AgentCoordinator coordinator = new AgentCoordinator();
        assertTrue(coordinator.registerAgent("AI-03", "Future", "queued"));
        assertTrue(coordinator.assignMission("m3", "AI-03", "future"));
        assertFalse(new AgentToolDispatcher(coordinator)
                .bindInvoker("AI-03", (tool, version, input) -> new JSONObject()));
    }
}
