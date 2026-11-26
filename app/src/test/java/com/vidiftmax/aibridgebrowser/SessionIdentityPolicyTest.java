package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import java.util.Arrays;
import java.util.Collections;
import org.junit.Test;

public class SessionIdentityPolicyTest {
    @Test public void acceptsNewNonEmptyIdentity() {
        assertTrue(SessionIdentityPolicy.isUnique("profile-ai-02", Arrays.asList("profile-ai-01")));
    }

    @Test public void rejectsDuplicateTabOrProfileIdentity() {
        assertFalse(SessionIdentityPolicy.isUnique("profile-ai-01", Arrays.asList("profile-ai-01")));
    }

    @Test public void rejectsNullBlankAndUnknownExistingSet() {
        assertFalse(SessionIdentityPolicy.isUnique(null, Collections.<String>emptyList()));
        assertFalse(SessionIdentityPolicy.isUnique("  ", Collections.<String>emptyList()));
        assertFalse(SessionIdentityPolicy.isUnique("profile", null));
    }
}
