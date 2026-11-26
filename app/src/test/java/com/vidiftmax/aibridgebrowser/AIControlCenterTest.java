package com.vidiftmax.aibridgebrowser;
import static org.junit.Assert.*;
import org.junit.Test;

public class AIControlCenterTest {
    @Test public void supportsAtMostTwentyDynamicAiAccounts() {
        AIControlCenter center = new AIControlCenter();
        for (int i = 1; i <= 20; i++) assertTrue(center.register(String.format(java.util.Locale.ROOT, "AI-%02d", i), "tab-" + i, "profile-" + i));
        assertEquals(20, center.panels().size());
        assertFalse(center.register("AI-21", "tab-21", "profile-21"));
    }
    @Test public void bindsByStableTabAndProfileIdentity() {
        AIControlCenter center = new AIControlCenter();
        assertTrue(center.register("AI-01", "tab-a", "profile-a"));
        assertFalse(center.beginMessage("tab-a", "profile-b", "mission"));
        assertTrue(center.beginMessage("tab-a", "profile-a", "mission"));
    }

    @Test public void refusesToBindTwoAiAccountsToTheSameWebViewProfile() {
        AIControlCenter center = new AIControlCenter();
        assertTrue(center.register("AI-01", "tab-a", "shared-profile"));
        assertFalse(center.register("AI-02", "tab-b", "shared-profile"));
        assertEquals(1, center.panels().size());
    }

    @Test public void ai01AndAi02UseDistinctTabAndProfileIdentities() {
        AIControlCenter center = new AIControlCenter();
        assertTrue(center.register("AI-01", "tab-ai-01", "profile-ai-01"));
        assertTrue(center.register("AI-02", "tab-ai-02", "profile-ai-02"));
        assertFalse(center.beginMessage("tab-ai-01", "profile-ai-02", "cross-profile"));
        assertFalse(center.beginMessage("tab-ai-02", "profile-ai-01", "cross-profile"));
        assertEquals("AI-01", center.panels().get(0).aiId);
        assertEquals("AI-02", center.panels().get(1).aiId);
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

    @Test public void restoresCompletedPanelIdentityAndEvidence() {
        AIControlCenter center = new AIControlCenter();
        assertTrue(center.restorePanel("AI-04", "tab-z", "profile-z",
                "RESPONSE_COMPLETE", "CRITICAL", "last two lines", "",
                true));
        AIControlCenter.Panel panel = center.panels().get(0);
        assertEquals("AI-04", panel.aiId);
        assertEquals("last two lines", panel.responseTail);
        assertEquals(AIControlCenter.ContextState.CRITICAL, panel.contextState);
        assertTrue(panel.reportConfirmed);
    }

    @Test public void restoresInFlightPanelAsUnknownNotResponding() {
        AIControlCenter center = new AIControlCenter();
        assertTrue(center.restorePanel("AI-02", "tab-b", "profile-b",
                "RESPONDING", "NORMAL", "partial tail", "mission still pending",
                false));
        AIControlCenter.Panel panel = center.panels().get(0);
        assertEquals(AIControlCenter.ResponseState.UNKNOWN, panel.responseState);
        assertEquals("mission still pending", panel.pendingMessage);
        assertFalse(panel.reportConfirmed);
    }

    @Test public void restoresSavedPanelOrderAndIdentity() {
        AIControlCenter center = new AIControlCenter();
        center.register("AI-01", "tab-a", "profile-a");
        center.register("AI-02", "tab-b", "profile-b");
        assertTrue(center.restorePanel("AI-05", "tab-a", "profile-a",
                "IDLE", "UNKNOWN", "", "", false));
        assertEquals("AI-05", center.panels().get(0).aiId);
        assertEquals("AI-02", center.panels().get(1).aiId);
    }

    @Test public void rebuildsPersistedPanelIdsWithoutTemporaryIdCollisions() {
        AIControlCenter center = new AIControlCenter();
        center.register("AI-01", "tab-a", "profile-a");
        center.register("AI-02", "tab-b", "profile-b");
        center.clear();
        assertTrue(center.restorePanel("AI-02", "tab-a", "profile-a",
                "IDLE", "UNKNOWN", "", "", false));
        assertTrue(center.restorePanel("AI-01", "tab-b", "profile-b",
                "IDLE", "UNKNOWN", "", "", false));
        assertEquals("AI-02", center.panels().get(0).aiId);
        assertEquals("AI-01", center.panels().get(1).aiId);
    }

}