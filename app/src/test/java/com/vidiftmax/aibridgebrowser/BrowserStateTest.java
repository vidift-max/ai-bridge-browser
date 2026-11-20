package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import java.util.Arrays;
import org.junit.Test;

public class BrowserStateTest {
    @Test public void rejectsDuplicateAndBlankTabIds() {
        BrowserState state = new BrowserState();
        state.addTab("tab-1");
        state.addTab("tab-1");
        state.addTab(" ");
        assertEquals(Arrays.asList("tab-1"), state.getTabIds());
        assertEquals(0, state.getActiveIndex());
    }

    @Test public void activeIndexFollowsSelectionAndRemoval() {
        BrowserState state = new BrowserState();
        state.addTab("a");
        state.addTab("b");
        state.addTab("c");
        assertTrue(state.selectTab(1));
        assertEquals(1, state.getActiveIndex());
        assertTrue(state.removeTab("b"));
        assertEquals(1, state.getActiveIndex());
        assertFalse(state.selectTab(5));
    }

    @Test public void replaceTabsClampsActiveIndexAndKeepsPauseState() {
        BrowserState state = new BrowserState();
        state.replaceTabs(Arrays.asList("a", "b"), 99, true);
        assertEquals(1, state.getActiveIndex());
        assertTrue(state.isPaused());
    }
}