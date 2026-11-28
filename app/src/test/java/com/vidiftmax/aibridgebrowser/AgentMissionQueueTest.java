package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class AgentMissionQueueTest {
    @Test public void claimsFifoOnlyForTheTwoAuthorizedProviderSessions() {
        AgentMissionQueue queue = new AgentMissionQueue();
        assertTrue(queue.enqueue("m03", "AI-03", "logical queued work"));
        assertTrue(queue.enqueue("m01", "AI-01", "first active work"));
        assertTrue(queue.enqueue("m02", "AI-02", "second active work"));
        assertEquals("m01", queue.claimNext().missionId);
        assertEquals("m02", queue.claimNext().missionId);
        assertNull(queue.claimNext());
        assertEquals(2, queue.activeCount());
        assertTrue(queue.complete("m01"));
        assertNull(queue.claimNext());
        assertTrue(queue.complete("m02"));
        assertNull(queue.claimNext()); // AI-03 stays queued, not silently activated.
    }

    @Test public void preventsDuplicateIdsAndCancelsOnlyPendingWork() {
        AgentMissionQueue queue = new AgentMissionQueue();
        assertTrue(queue.enqueue("m1", "AI-01", "task"));
        assertFalse(queue.enqueue("m1", "AI-02", "duplicate"));
        AgentMissionQueue.Mission mission = queue.claimNext();
        assertNotNull(mission);
        assertFalse(queue.cancel("m1"));
        assertTrue(queue.complete("m1"));
        assertFalse(queue.complete("m1"));
    }

    @Test public void rejectsMalformedAndOversizedMissions() {
        AgentMissionQueue queue = new AgentMissionQueue();
        assertFalse(queue.enqueue("", "AI-01", "task"));
        assertFalse(queue.enqueue("m", "AI-21", "task"));
        assertFalse(queue.enqueue("m", "AI-01", " "));
        assertFalse(queue.enqueue("m2", "AI-01", new String(new char[5001]).replace('\0', 'x')));
    }
}
