package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import org.junit.Test;

public class UpdaterUiPolicyTest {
    @Test public void deliversWhileActivityIsActive() {
        assertTrue(UpdaterUiPolicy.shouldDeliver(false, false, false));
    }
    @Test public void rejectsAfterExplicitTeardown() {
        assertFalse(UpdaterUiPolicy.shouldDeliver(true, false, false));
    }
    @Test public void rejectsWhileFinishing() {
        assertFalse(UpdaterUiPolicy.shouldDeliver(false, true, false));
    }
    @Test public void rejectsAfterFrameworkDestroy() {
        assertFalse(UpdaterUiPolicy.shouldDeliver(false, false, true));
    }
}
