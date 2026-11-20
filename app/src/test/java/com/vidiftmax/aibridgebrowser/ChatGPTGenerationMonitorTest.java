package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class ChatGPTGenerationMonitorTest {
    @Test public void doesNotAssumeInitialAbsenceMeansComplete() {
        ChatGPTGenerationMonitor monitor = new ChatGPTGenerationMonitor();
        assertEquals(ChatGPTGenerationMonitor.State.UNKNOWN,
                monitor.observe(ChatGPTGenerationMonitor.Observation.NOT_GENERATING));
    }

    @Test public void requiresTwoConsecutiveAbsenceObservationsAfterGeneration() {
        ChatGPTGenerationMonitor monitor = new ChatGPTGenerationMonitor();
        assertEquals(ChatGPTGenerationMonitor.State.RESPONDING,
                monitor.observe(ChatGPTGenerationMonitor.Observation.GENERATING));
        assertEquals(ChatGPTGenerationMonitor.State.RESPONDING,
                monitor.observe(ChatGPTGenerationMonitor.Observation.NOT_GENERATING));
        assertEquals(ChatGPTGenerationMonitor.State.RESPONSE_COMPLETE,
                monitor.observe(ChatGPTGenerationMonitor.Observation.NOT_GENERATING));
    }

    @Test public void unknownObservationBreaksAbsenceSequence() {
        ChatGPTGenerationMonitor monitor = new ChatGPTGenerationMonitor();
        monitor.observe(ChatGPTGenerationMonitor.Observation.GENERATING);
        monitor.observe(ChatGPTGenerationMonitor.Observation.NOT_GENERATING);
        assertEquals(ChatGPTGenerationMonitor.State.RESPONDING,
                monitor.observe(ChatGPTGenerationMonitor.Observation.UNKNOWN));
        assertEquals(ChatGPTGenerationMonitor.State.RESPONDING,
                monitor.observe(ChatGPTGenerationMonitor.Observation.NOT_GENERATING));
    }

    @Test public void renewedGenerationReturnsToResponding() {
        ChatGPTGenerationMonitor monitor = new ChatGPTGenerationMonitor();
        monitor.observe(ChatGPTGenerationMonitor.Observation.GENERATING);
        monitor.observe(ChatGPTGenerationMonitor.Observation.NOT_GENERATING);
        monitor.observe(ChatGPTGenerationMonitor.Observation.NOT_GENERATING);
        assertEquals(ChatGPTGenerationMonitor.State.RESPONDING,
                monitor.observe(ChatGPTGenerationMonitor.Observation.GENERATING));
    }

    @Test public void parsesOnlyKnownSignals() {
        assertEquals(ChatGPTGenerationMonitor.Observation.GENERATING,
                ChatGPTGenerationMonitor.parse("GENERATING"));
        assertEquals(ChatGPTGenerationMonitor.Observation.NOT_GENERATING,
                ChatGPTGenerationMonitor.parse("NOT_GENERATING"));
        assertEquals(ChatGPTGenerationMonitor.Observation.UNKNOWN,
                ChatGPTGenerationMonitor.parse("anything else"));
    }
}
