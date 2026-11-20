package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

/** In-memory model for checkpoints waiting for an authorized delivery/ack. */
final class CheckpointQueue {
    static final class Item {
        final String eventId;
        final RoundCheckpoint checkpoint;
        boolean acknowledged;

        Item(RoundCheckpoint checkpoint) {
            if (checkpoint == null) throw new IllegalArgumentException("checkpoint");
            this.eventId = UUID.randomUUID().toString();
            this.checkpoint = checkpoint;
        }

        Item(String eventId, RoundCheckpoint checkpoint, boolean acknowledged) {
            if (eventId == null || eventId.trim().isEmpty()) throw new IllegalArgumentException("eventId");
            if (checkpoint == null) throw new IllegalArgumentException("checkpoint");
            this.eventId = eventId;
            this.checkpoint = checkpoint;
            this.acknowledged = acknowledged;
        }
    }

    private final List<Item> items = new ArrayList<>();

    Item enqueue(RoundCheckpoint checkpoint) {
        Item item = new Item(checkpoint);
        items.add(item);
        return item;
    }

    List<Item> pending() {
        List<Item> result = new ArrayList<>();
        for (Item item : items) {
            if (!item.acknowledged) result.add(item);
        }
        return Collections.unmodifiableList(result);
    }

    CheckpointQueueSnapshot snapshot() {
        List<CheckpointQueueSnapshot.Entry> entries = new ArrayList<>();
        for (Item item : items) {
            entries.add(new CheckpointQueueSnapshot.Entry(
                    item.eventId, item.checkpoint, item.acknowledged));
        }
        return new CheckpointQueueSnapshot(entries);
    }

    static CheckpointQueue restore(CheckpointQueueSnapshot snapshot) {
        if (snapshot == null) throw new IllegalArgumentException("snapshot");
        CheckpointQueue queue = new CheckpointQueue();
        for (CheckpointQueueSnapshot.Entry entry : snapshot.entries) {
            queue.items.add(new Item(entry.eventId, entry.checkpoint, entry.acknowledged));
        }
        return queue;
    }

    boolean acknowledge(String eventId) {
        for (Item item : items) {
            if (item.eventId.equals(eventId) && !item.acknowledged) {
                item.acknowledged = true;
                return true;
            }
        }
        return false;
    }

    int pendingCount() {
        return pending().size();
    }
}
