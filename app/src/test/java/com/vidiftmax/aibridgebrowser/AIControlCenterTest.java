package com.vidiftmax.aibridgebrowser;
import static org.junit.Assert.*;
import org.junit.Test;

public class AIControlCenterTest {
    @Test public void supportsAtMostSixDynamicAiTabs() {
        AIControlCenter center = new AIControlCenter();
        for (int i = 1; i <= 6; i++) assertTrue(center.register("AI-" + i, "tab-" + i, "profile-" + i));
        assertEquals(6, center.panels().size());
        assertFalse(center.register("AI-07", "tab-7", "profile-7"));
    }
    @Test public void bindsByStableTabAndProfileIdentity() {
        AIControlCenter center = new AIControlCenter();
        assertTrue(center.register("AI-01", "tab-a", "profile-a"));
        assertFalse(center.beginMessage("tab-a", "profile-b", "mission"));
        assertTrue(center.beginMessage("tab-a", "profile-a", "mission"));
    }
    @Test public void newMessageClearsTailAndCapturesOnlyLastTwoLines() {
        AIControlCenter center = new AIControlCenter(); center.register("AI-01", "tab-a", "profile-a");
        assertTrue(center.beginMessage("tab-a", "profile-a", "first"));
        assertTrue(center.markResponding("tab-a", "profile-a"));
        assertTrue(center.completeResponse("tab-a", "profile-a", "line one\nline two\nline three"));
        assertEquals("line two\nline three", center.panels().get(0).responseTail);
        assertTrue(center.beginMessage("tab-a", "profile-a", "second"));
        assertEquals("", center.panels().get(0).responseTail);
        assertFalse(center.panels().get(0).reportConfirmed);
    }
    @Test public void reportRequiresCompletedResponseAndContextIsPerAi() {
        AIControlCenter center = new AIControlCenter();
        center.register("AI-01", "tab-a", "profile-a"); center.register("AI-02", "tab-b", "profile-b");
        assertFalse(center.confirmReport("tab-a", "profile-a"));
        assertTrue(center.setContextState("tab-b", "profile-b", AIControlCenter.ContextState.FULL));
        assertEquals(AIControlCenter.ContextState.FULL, center.panels().get(1).contextState);
        assertTrue(center.beginMessage("tab-a", "profile-a", "mission"));
        assertTrue(center.markResponding("tab-a", "profile-a"));
        assertTrue(center.completeResponse("tab-a", "profile-a", "done"));
        assertTrue(center.confirmReport("tab-a", "profile-a"));
        assertFalse(center.panels().get(1).reportConfirmed);
    }
    @Test public void unregisterLeavesOtherPanelsUntouched() {
        AIControlCenter center = new AIControlCenter();
        center.register("AI-01", "tab-a", "profile-a"); center.register("AI-02", "tab-b", "profile-b");
        assertTrue(center.unregisterByTab("tab-a"));
        assertEquals("AI-02", center.panels().get(0).aiId);
    }
    @Test public void generationMonitorIsIndependentForEachPanel() {
        AIControlCenter center = new AIControlCenter();
        center.register("AI-01", "tab-a", "profile-a");
        center.register("AI-02", "tab-b", "profile-b");
        assertTrue(center.beginMessage("tab-a", "profile-a", "mission A"));
        assertTrue(center.beginMessage("tab-b", "profile-b", "mission B"));

        assertTrue(center.observeGeneration("tab-a", "profile-a",
                ChatGPTGenerationMonitor.Observation.GENERATING));
        assertEquals(AIControlCenter.ResponseState.RESPONDING,
                center.panels().get(0).responseState);
        assertEquals(AIControlCenter.ResponseState.SENDING,
                center.panels().get(1).responseState);

        assertTrue(center.observeGeneration("tab-a", "profile-a",
                ChatGPTGenerationMonitor.Observation.NOT_GENERATING));
        assertTrue(center.observeGeneration("tab-a", "profile-a",
                ChatGPTGenerationMonitor.Observation.NOT_GENERATING));
        assertEquals(AIControlCenter.ResponseState.RESPONSE_COMPLETE,
                center.panels().get(0).responseState);
        assertEquals(AIControlCenter.ResponseState.SENDING,
                center.panels().get(1).responseState);
    }

    @Test public void unknownGenerationSignalNeverCompletesMission() {
        AIControlCenter center = new AIControlCenter();
        center.register("AI-01", "tab-a", "profile-a");
        assertTrue(center.beginMessage("tab-a", "profile-a", "mission"));
        assertTrue(center.observeGeneration("tab-a", "profile-a",
                ChatGPTGenerationMonitor.Observation.NOT_GENERATING));
        assertEquals(AIControlCenter.ResponseState.UNKNOWN,
                center.panels().get(0).responseState);
        assertFalse(center.confirmReport("tab-a", "profile-a"));
    }

    @Test public void capturesResponseTailOnlyAfterObservedCompletion() {
        AIControlCenter center = new AIControlCenter();
        center.register("AI-01", "tab-a", "profile-a");
        assertTrue(center.beginMessage("tab-a", "profile-a", "mission"));
        assertFalse(center.captureCompletedResponseTail("tab-a", "profile-a", "early"));
        center.observeGeneration("tab-a", "profile-a",
                ChatGPTGenerationMonitor.Observation.GENERATING);
        center.observeGeneration("tab-a", "profile-a",
                ChatGPTGenerationMonitor.Observation.NOT_GENERATING);
        center.observeGeneration("tab-a", "profile-a",
                ChatGPTGenerationMonitor.Observation.NOT_GENERATING);
        assertTrue(center.captureCompletedResponseTail("tab-a", "profile-a",
                "line one\nline two\nline three"));
        assertEquals("line two\nline three", center.panels().get(0).responseTail);
    }

}