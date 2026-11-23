package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import org.junit.Test;

public class AudioMonitorTest {
    @Test public void playbackCanBeToggledWithoutStartingMicrophone() {
        AudioMonitor monitor = new AudioMonitor();
        assertTrue(monitor.isPlaybackEnabled());
        assertFalse(monitor.isRunning());
        monitor.setPlaybackEnabled(false);
        assertFalse(monitor.isPlaybackEnabled());
        monitor.setPlaybackEnabled(true);
        assertTrue(monitor.isPlaybackEnabled());
        assertFalse(monitor.isRunning());
    }
}