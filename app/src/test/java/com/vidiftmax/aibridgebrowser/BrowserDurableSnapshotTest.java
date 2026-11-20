package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import java.util.Collections;
import org.junit.Test;

public class BrowserDurableSnapshotTest {
    @Test public void combinesBrowserAndCheckpointRecoveryState() {
        BrowserState browser = new BrowserState();
        browser.addTab("tab-1");
        browser.setPaused(true);

        RoundCheckpoint checkpoint = new RoundCheckpoint(
                "room-1", 1, 10,
                Collections.singletonList(
                        new RoundCheckpoint.Entry("IA-01","m1","DONE","report/1")));
        CheckpointQueue queue = new CheckpointQueue();
        queue.enqueue(checkpoint);

        BrowserDurableSnapshot snapshot =
                new BrowserDurableSnapshot(browser, queue.snapshot());

        assertEquals(1, snapshot.browserState.getTabIds().size());
        assertTrue(snapshot.browserState.isPaused());
        assertEquals(1, snapshot.checkpointQueue.entries.size());

        CheckpointQueue restored =
                CheckpointQueue.restore(snapshot.checkpointQueue);
        assertEquals(1, restored.pendingCount());
    }
}