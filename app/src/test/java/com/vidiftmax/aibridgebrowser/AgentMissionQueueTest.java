package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class AgentMissionQueueTest {
    @Test public void fifoSchedulerNeverRunsMoreThanTwoMissions() {
        AgentMissionQueue queue = new AgentMissionQueue();
        assertTrue(queue.enqueue("m1", "AI-01", "first"));
        assertTrue(queue.enqueue("m2", "AI-02", "second"));
        assertTrue(queue.enqueue("m3", "AI-03", "third"));
        assertEquals("m1", queue.claimNext().missionId);
        assertEquals("m2", queue.claimNext().missionId);
        assertNull(queue.claimNext());
        assertEquals(2, queue.activeCount());
        assertTrue(queue.complete("m1"));
        assertEquals("m3", queue.claimNext().missionId);
        assertEquals(2, queue.activeCount());
    }

    @Test public void rejectsDuplicateMissionIdsAndInvalidAgents() {
        AgentMissionQueue queue = new AgentMissionQueue();
        assertTrue(queue.enqueue("m1", "AI-01", "task"));
        assertFalse(queue.enqueue("m1", "AI-02", "duplicate id"));
        assertFalse(queue.enqueue("m2", "AI-21", "unknown agent"));
        assertFalse(queue.enqueue("m3", "AI-02", " "));
        assertEquals(1, queue.all().size());
    }

    @Test public void cancellationOnlyAppliesToQueuedMissions() {
        AgentMissionQueue queue = new AgentMissionQueue();
        assertTrue(queue.enqueue("m1", "AI-01", "first"));
        assertTrue(queue.enqueue("m2", "AI-02", "second"));
        assertTrue(queue.cancel("m1"));
        assertFalse(queue.cancel("m1"));
        assertEquals("m2", queue.claimNext().missionId);
        assertFalse(queue.cancel("m2"));
        assertEquals(AgentMissionQueue.State.CANCELLED, queue.all().get(0).state);
    }

    @Test public void completionOnlyAppliesToRunningMissions() {
        AgentMissionQueue queue = new AgentMissionQueue();
        assertTrue(queue.enqueue("m1", "AI-01", "first"));
        assertFalse(queue.complete("m1"));
        queue.claimNext();
        assertTrue(queue.complete("m1"));
        assertFalse(queue.complete("m1"));
        assertEquals(AgentMissionQueue.State.COMPLETED, queue.all().get(0).state);
    }

    @Test public void returnedMissionListCannotBeModified() {
        AgentMissionQueue queue = new AgentMissionQueue();
        queue.enqueue("m1", "AI-01", "first");
        try {
            queue.all().clear();
            fail("mission_snapshot_must_be_unmodifiable");
        } catch (UnsupportedOperationException expected) {
            assertEquals(1, queue.all().size());
        }
    }
}
