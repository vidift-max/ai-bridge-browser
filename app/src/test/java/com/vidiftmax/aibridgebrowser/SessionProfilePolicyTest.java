package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import java.util.Arrays;
import java.util.Collections;
import org.junit.Test;

public class SessionProfilePolicyTest {
    @Test public void acceptsUniqueNonEmptyProfileId() {
        assertTrue(SessionProfilePolicy.hasUniqueProfileId("profile-ai-01", Arrays.asList("profile-ai-02", "profile-ai-03")));
    }
    @Test public void rejectsDuplicateProfileId() {
        assertFalse(SessionProfilePolicy.hasUniqueProfileId("profile-ai-01", Arrays.asList("profile-ai-01", "profile-ai-02")));
    }
    @Test public void rejectsNullOrBlankProfileId() {
        assertFalse(SessionProfilePolicy.hasUniqueProfileId(null, Collections.emptyList()));
        assertFalse(SessionProfilePolicy.hasUniqueProfileId("  ", Collections.emptyList()));
    }
    @Test public void allowsUniqueIdWhenNoProfilesExistYet() {
        assertTrue(SessionProfilePolicy.hasUniqueProfileId("profile-first", Collections.emptyList()));
    }
    @Test public void isolationClaimRequiresFeatureAssignmentAndUniqueIdentity() {
        assertTrue(SessionProfilePolicy.canClaimProfileIsolation(true, true, true));
        assertFalse(SessionProfilePolicy.canClaimProfileIsolation(false, true, true));
        assertFalse(SessionProfilePolicy.canClaimProfileIsolation(true, false, true));
        assertFalse(SessionProfilePolicy.canClaimProfileIsolation(true, true, false));
    }
    @Test public void duplicateOrUnsupportedProfileNeverQualifiesForSeparateAccounts() {
        assertFalse(SessionProfilePolicy.canClaimProfileIsolation(true, true,
                SessionProfilePolicy.hasUniqueProfileId("same", Arrays.asList("same"))));
        assertFalse(SessionProfilePolicy.canClaimProfileIsolation(false, false, true));
    }
}
