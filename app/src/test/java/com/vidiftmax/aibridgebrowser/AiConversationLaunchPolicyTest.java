package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public final class AiConversationLaunchPolicyTest {
    private String ready() {
        return AiConversationLaunchPolicy.blockingReason(
                true, true, true, true, true, true, true);
    }

    @Test public void readyPairCanProceedToExplicitAccountConfirmation() {
        assertNull(ready());
    }

    @Test public void bothAiIdentitiesMustBeAssigned() {
        assertEquals("AI_IDENTITIES_NOT_ASSIGNED",
                AiConversationLaunchPolicy.blockingReason(false, true, true, true, true, true, true));
        assertEquals("AI_IDENTITIES_NOT_ASSIGNED",
                AiConversationLaunchPolicy.blockingReason(true, false, true, true, true, true, true));
    }

    @Test public void tabsAndProfilesMustBeDistinct() {
        assertEquals("TABS_NOT_DISTINCT",
                AiConversationLaunchPolicy.blockingReason(true, true, false, true, true, true, true));
        assertEquals("PROFILES_NOT_DISTINCT",
                AiConversationLaunchPolicy.blockingReason(true, true, true, false, true, true, true));
    }

    @Test public void profileIsolationMustBeVerified() {
        assertEquals("PROFILE_ISOLATION_UNVERIFIED",
                AiConversationLaunchPolicy.blockingReason(true, true, true, true, false, true, true));
    }

    @Test public void bothPagesMustFinishLoading() {
        assertEquals("PAGES_NOT_READY",
                AiConversationLaunchPolicy.blockingReason(true, true, true, true, true, false, true));
    }

    @Test public void bothTabsMustBeOnChatGpt() {
        assertEquals("CHATGPT_NOT_OPEN",
                AiConversationLaunchPolicy.blockingReason(true, true, true, true, true, true, false));
    }

    @Test public void firstFailureIsReportedDeterministically() {
        assertEquals("AI_IDENTITIES_NOT_ASSIGNED",
                AiConversationLaunchPolicy.blockingReason(false, false, false, false, false, false, false));
    }

    @Test public void evidenceAcceptsOnlySequentialAlternatingTurnsAndHashesBodies() {
        AiBridgeEvidence evidence = new AiBridgeEvidence();
        assertTrue(evidence.addTurn(1, "AI-01", "hello"));
        assertTrue(evidence.addTurn(2, "AI-02", "world"));
        assertEquals(2, evidence.turnCount());
        assertTrue(evidence.isAlternatingPair());
        assertEquals(64, evidence.events().get(0).responseSha256.length());
        assertEquals("2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
                evidence.events().get(0).responseSha256);
        assertEquals(5, evidence.events().get(0).responseChars);
    }

    @Test public void evidenceRejectsWrongSenderGapDuplicateAndEmptyResponse() {
        AiBridgeEvidence evidence = new AiBridgeEvidence();
        assertFalse(evidence.addTurn(1, "AI-02", "wrong sender"));
        assertFalse(evidence.addTurn(2, "AI-02", "gap"));
        assertFalse(evidence.addTurn(1, "AI-01", "  "));
        assertTrue(evidence.addTurn(1, "AI-01", "first"));
        assertFalse(evidence.addTurn(1, "AI-01", "duplicate"));
        assertFalse(evidence.addTurn(3, "AI-01", "gap"));
        assertEquals(1, evidence.turnCount());
    }

    @Test public void evidenceEventsAreReadOnlyAndCanBeReset() {
        AiBridgeEvidence evidence = new AiBridgeEvidence();
        assertTrue(evidence.addTurn(1, "AI-01", "first"));
        try {
            evidence.events().clear();
            fail("events must be immutable");
        } catch (UnsupportedOperationException expected) {
            assertEquals(1, evidence.turnCount());
        }
        evidence.clear();
        assertEquals(0, evidence.turnCount());
        assertTrue(evidence.addTurn(1, "AI-01", "new run"));
    }
}
