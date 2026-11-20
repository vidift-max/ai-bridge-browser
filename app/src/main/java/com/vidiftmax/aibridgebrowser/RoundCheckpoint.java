package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Immutable aggregated checkpoint for one mission round. */
final class RoundCheckpoint {
    static final class Entry {
        final String aiId;
        final String missionId;
        final String status;
        final String reportUrl;

        Entry(String aiId, String missionId, String status, String reportUrl) {
            this.aiId = aiId;
            this.missionId = missionId;
            this.status = status;
            this.reportUrl = reportUrl;
        }
    }

    final String roomId;
    final int round;
    final int totalRounds;
    final List<Entry> entries;

    RoundCheckpoint(String roomId, int round, int totalRounds, List<Entry> entries) {
        if (roomId == null || roomId.trim().isEmpty()) throw new IllegalArgumentException("roomId");
        if (round < 1 || totalRounds < round) throw new IllegalArgumentException("round");
        if (entries == null) throw new IllegalArgumentException("entries");
        this.roomId = roomId;
        this.round = round;
        this.totalRounds = totalRounds;
        this.entries = Collections.unmodifiableList(new ArrayList<>(entries));
    }

    int doneCount() {
        return countStatus("DONE");
    }

    int blockedCount() {
        return countStatus("BLOCKED");
    }

    boolean complete() {
        return !entries.isEmpty() && doneCount() == entries.size();
    }

    String roundLabel() {
        return round + "/" + totalRounds;
    }

    private int countStatus(String status) {
        int count = 0;
        for (Entry entry : entries) {
            if (status.equals(entry.status)) count++;
        }
        return count;
    }
}
