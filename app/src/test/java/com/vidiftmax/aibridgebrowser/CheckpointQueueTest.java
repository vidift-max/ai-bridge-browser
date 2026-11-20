package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import java.util.Collections;
import org.junit.Test;

public class CheckpointQueueTest {
    @Test public void keepsCheckpointPendingUntilAcknowledged() {
        RoundCheckpoint checkpoint = new RoundCheckpoint(
                "room-1", 1, 10,
                Collections.singletonList(
                        new RoundCheckpoint.Entry("IA-01","m1","DONE","report/1")));

        CheckpointQueue queue = new CheckpointQueue();
        CheckpointQueue.Item item = queue.enqueue(checkpoint);

        assertEquals(1, queue.pendingCount());
        assertFalse(item.acknowledged);
        assertTrue(queue.acknowledge(item.eventId));
        assertTrue(item.acknowledged);
        assertEquals(0, queue.pendingCount());
        assertFalse(queue.acknowledge(item.eventId));
    }
}