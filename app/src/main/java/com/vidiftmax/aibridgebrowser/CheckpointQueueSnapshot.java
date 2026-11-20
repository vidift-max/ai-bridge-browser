package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Serializable-neutral snapshot of checkpoint queue state.
 * Persistence adapters can store this snapshot without coupling the queue
 * to a database, filesystem, or network provider.
 */
final class CheckpointQueueSnapshot {
    static final class Entry {
        final String eventId;
        final RoundCheckpoint checkpoint;
        final boolean acknowledged;

        Entry(String eventId, RoundCheckpoint checkpoint, boolean acknowledged) {
            if (eventId == null || eventId.trim().isEmpty()) {
                throw new IllegalArgumentException("eventId");
            }
            if (checkpoint == null) throw new IllegalArgumentException("checkpoint");
            this.eventId = eventId;
            this.checkpoint = checkpoint;
            this.acknowledged = acknowledged;
        }
    }

    final List<Entry> entries;

    CheckpointQueueSnapshot(List<Entry> entries) {
        if (entries == null) throw new IllegalArgumentException("entries");
        this.entries = Collections.unmodifiableList(new ArrayList<>(entries));
    }
}
