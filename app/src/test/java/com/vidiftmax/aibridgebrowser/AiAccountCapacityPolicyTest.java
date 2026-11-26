package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class AiAccountCapacityPolicyTest {
    @Test public void productCeilingIsTwenty() {
        assertTrue(AiAccountCapacityPolicy.supportsAccountCount(20));
        assertFalse(AiAccountCapacityPolicy.supportsAccountCount(21));
        assertFalse(AiAccountCapacityPolicy.supportsAccountCount(0));
    }

    @Test public void currentMissionRestoresOnlyAi01AndAi02() {
        assertTrue(AiAccountCapacityPolicy.isCurrentMissionAccountId("AI-01"));
        assertTrue(AiAccountCapacityPolicy.isCurrentMissionAccountId("AI-02"));
        assertFalse(AiAccountCapacityPolicy.isCurrentMissionAccountId("AI-03"));
        assertFalse(AiAccountCapacityPolicy.isCurrentMissionAccountId("AI-20"));
        assertFalse(AiAccountCapacityPolicy.isCurrentMissionAccountId(null));
    }

    @Test public void currentMissionActivatesOnlyTwoAccounts() {
        assertTrue(AiAccountCapacityPolicy.canActivate(0));
        assertTrue(AiAccountCapacityPolicy.canActivate(1));
        assertFalse(AiAccountCapacityPolicy.canActivate(2));
        assertFalse(AiAccountCapacityPolicy.canActivate(3));
        assertFalse(AiAccountCapacityPolicy.canActivate(-1));
    }
}
