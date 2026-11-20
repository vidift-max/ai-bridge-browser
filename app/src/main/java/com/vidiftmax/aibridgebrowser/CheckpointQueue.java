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
