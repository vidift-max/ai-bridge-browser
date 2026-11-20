package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Coordinates round completion without provider-specific delivery. */
final class MissionCoordinator {
    static final class RoundSummary {
        final String roomId;
        final int round;
        final int totalAssignments;
        final int doneAssignments;
        final int blockedAssignments;
        final int pendingAssignments;
        final int runningAssignments;
        final boolean complete;

        RoundSummary(String roomId, int round, int totalAssignments, int doneAssignments,
                     int blockedAssignments, int pendingAssignments, int runningAssignments,
                     boolean complete) {
            this.roomId = roomId;
            this.round = round;
            this.totalAssignments = totalAssignments;
            this.doneAssignments = doneAssignments;
            this.blockedAssignments = blockedAssignments;
            this.pendingAssignments = pendingAssignments;
            this.runningAssignments = runningAssignments;
            this.complete = complete;
        }
    }

    private final MissionRoom room;

    MissionCoordinator(MissionRoom room) {
        if (room == null) throw new IllegalArgumentException("room");
        this.room = room;
    }

    RoundSummary checkpoint(int round) {
        if (round < 1) throw new IllegalArgumentException("round");
        return new RoundSummary(room.getRoomId(), round, room.countForRound(round),
                room.doneCount(round), room.blockedCount(round), room.pendingCount(round),
                room.runningCount(round), room.isRoundComplete(round));
    }

    RoundCheckpoint aggregatedCheckpoint(int round) {
        if (round < 1) throw new IllegalArgumentException("round");
        List<RoundCheckpoint.Entry> entries = new ArrayList<>();
        int totalRounds = 0;
        for (MissionAssignment assignment : room.getAssignments()) {
            if (assignment.round == round) {
                totalRounds = Math.max(totalRounds, assignment.totalRounds);
                entries.add(new RoundCheckpoint.Entry(assignment.aiId, assignment.missionId,
                        assignment.status.name(), assignment.reportUrl));
            }
        }
        return new RoundCheckpoint(room.getRoomId(), round, totalRounds, entries);
    }

    boolean canAdvance(int round) { return checkpoint(round).complete; }

    List<MissionAssignment> incomplete(int round) {
        if (round < 1) throw new IllegalArgumentException("round");
        List<MissionAssignment> result = new ArrayList<>();
        for (MissionAssignment assignment : room.getAssignments()) {
            if (assignment.round == round && !assignment.isComplete()) result.add(assignment);
        }
        return Collections.unmodifiableList(result);
    }
}
