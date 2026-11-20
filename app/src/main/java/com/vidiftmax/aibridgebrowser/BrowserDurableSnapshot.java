package com.vidiftmax.aibridgebrowser;

/**
 * Combined browser recovery snapshot boundary.
 * Contains browser UI state and the provider-neutral checkpoint queue state.
 */
final class BrowserDurableSnapshot {
    final BrowserState browserState;
    final CheckpointQueueSnapshot checkpointQueue;

    BrowserDurableSnapshot(BrowserState browserState, CheckpointQueueSnapshot checkpointQueue) {
        if (browserState == null) throw new IllegalArgumentException("browserState");
        if (checkpointQueue == null) throw new IllegalArgumentException("checkpointQueue");
        this.browserState = browserState;
        this.checkpointQueue = checkpointQueue;
    }
}
