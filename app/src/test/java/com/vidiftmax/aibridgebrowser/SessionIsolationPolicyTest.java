package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class SessionIsolationPolicyTest {
    @Test public void accountAssignmentRequiresActualMultiProfileAssignment() {
        assertTrue(SessionIsolationPolicy.canAssignAccount(true));
        assertFalse(SessionIsolationPolicy.canAssignAccount(false));
    }

    @Test public void assignedProfileMustMatchRequestedIdentity() {
        assertTrue(SessionIsolationPolicy.isAssignedProfile("profile-01", "profile-01"));
    }

    @Test public void assignedProfileRejectsMismatchOrMissingValue() {
        assertFalse(SessionIsolationPolicy.isAssignedProfile("profile-01", "profile-02"));
        assertFalse(SessionIsolationPolicy.isAssignedProfile("profile-01", null));
        assertFalse(SessionIsolationPolicy.isAssignedProfile(" ", " "));
    }

    @Test public void queueTargetRequiresExactTabAndProfilePair() {
        assertTrue(SessionIsolationPolicy.isQueueTargetCurrent(
                "tab-01", "profile-01", "tab-01", "profile-01"));
    }

    @Test public void queueTargetRejectsDifferentTabEvenWithSameProfile() {
        assertFalse(SessionIsolationPolicy.isQueueTargetCurrent(
                "tab-01", "profile-01", "tab-02", "profile-01"));
    }

    @Test public void queueTargetRejectsDifferentProfileEvenWithSameTab() {
        assertFalse(SessionIsolationPolicy.isQueueTargetCurrent(
                "tab-01", "profile-01", "tab-01", "profile-02"));
    }

    @Test public void queueTargetRejectsMissingOrBlankIdentity() {
        assertFalse(SessionIsolationPolicy.isQueueTargetCurrent(
                null, "profile-01", null, "profile-01"));
        assertFalse(SessionIsolationPolicy.isQueueTargetCurrent(
                "tab-01", " ", "tab-01", " "));
    }
}