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
}
