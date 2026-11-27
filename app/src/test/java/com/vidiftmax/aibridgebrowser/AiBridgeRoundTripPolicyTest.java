package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public final class AiBridgeRoundTripPolicyTest {
    @Test public void roundTripRequiresExactlyTwoActiveIdentities() {
        assertTrue(AiBridgeRoundTripPolicy.isAllowed(new String[]{"AI-01","AI-02"}));
        assertFalse(AiBridgeRoundTripPolicy.isAllowed(new String[]{"AI-01"}));
        assertFalse(AiBridgeRoundTripPolicy.isAllowed(new String[]{"AI-01","AI-02","AI-03"}));
    }

    @Test public void isolatedPairRequiresBothProfiles() {
        assertTrue(AiBridgeRoundTripPolicy.isIsolatedPairReady(
                new String[]{"AI-01","AI-02"}, true, true));
        assertFalse(AiBridgeRoundTripPolicy.isIsolatedPairReady(
                new String[]{"AI-01","AI-02"}, true, false));
        assertFalse(AiBridgeRoundTripPolicy.isIsolatedPairReady(
                new String[]{"AI-01","AI-03"}, true, true));
    }

    @Test public void turnLimitIsBounded() {
        assertTrue(AiBridgeRoundTripPolicy.isTurnCountAllowed(2));
        assertTrue(AiBridgeRoundTripPolicy.isTurnCountAllowed(10));
        assertTrue(AiBridgeRoundTripPolicy.isTurnCountAllowed(20));
        assertFalse(AiBridgeRoundTripPolicy.isTurnCountAllowed(1));
        assertFalse(AiBridgeRoundTripPolicy.isTurnCountAllowed(21));
    }

    @Test public void freshResponseMustRemainStableForThreeReads() {
        assertFalse(AiBridgeRoundTripPolicy.isStableFreshResponse("old", "new", "new", 2));
        assertTrue(AiBridgeRoundTripPolicy.isStableFreshResponse("old", "new", "new", 3));
        assertFalse(AiBridgeRoundTripPolicy.isStableFreshResponse("old", "partial", "new", 3));
        assertFalse(AiBridgeRoundTripPolicy.isStableFreshResponse("same", "same", "same", 3));
    }

    @Test public void responseMustChangeBeforeRelay() {
        assertFalse(AiBridgeRoundTripPolicy.isFreshResponse("same", "same"));
        assertTrue(AiBridgeRoundTripPolicy.isFreshResponse("old", "new"));
        assertFalse(AiBridgeRoundTripPolicy.isFreshResponse("", ""));
    }
}
