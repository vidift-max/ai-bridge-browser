package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class TabRecordTest {
    @Test public void newRecordHasStableIdentityAndLockedDefaults() {
        TabRecord record = new TabRecord("https://chatgpt.com/");
        assertNotNull(record.tabId);
        assertNotNull(record.profileId);
        assertFalse(record.tabId.isEmpty());
        assertFalse(record.profileId.isEmpty());
        assertTrue(record.locked);
        assertEquals("WAITING_PAGE", record.missionState);
        assertEquals("https://chatgpt.com/", record.url);
    }

    @Test public void restoredRecordKeepsIdentity() {
        TabRecord record = new TabRecord("tab-7", "profile-7", "https://example.com/");
        assertEquals("tab-7", record.tabId);
        assertEquals("profile-7", record.profileId);
        assertTrue(record.locked);
    }
}