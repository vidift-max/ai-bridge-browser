package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import java.util.Collections;
import org.junit.Test;

public class CheckpointQueueSnapshotTest {
    @Test public void restoresPendingAndAcknowledgedItems() {
        RoundCheckpoint checkpoint = new RoundCheckpoint(
                "room-1", 1, 10,
                Collections.singletonList(
                        new RoundCheckpoint.Entry("IA-01","m1","DONE","report/1")));

        CheckpointQueue queue = new CheckpointQueue();
        CheckpointQueue.Item pending = queue.enqueue(checkpoint);
        CheckpointQueue.Item acknowledged = queue.enqueue(checkpoint);
        assertTrue(queue.acknowledge(acknowledged.eventId));

        CheckpointQueue restored = CheckpointQueue.restore(queue.snapshot());

        assertEquals(1, restored.pendingCount());
        assertEquals(pending.eventId, restored.pending().get(0).eventId);
        assertTrue(restored.acknowledge(pending.eventId));
        assertEquals(0, restored.pendingCount());
    }
}