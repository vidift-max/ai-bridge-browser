package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Coordinates round completion without provider-specific delivery. */
final class MissionCoordinator {
    static final class RoundCheckpoint {
        final String roomId;
        final int round;
        final int totalAssignments;
        final int doneAssignments;
        final int blockedAssignments;
        final int pendingAssignments;
        final int runningAssignments;
        final boolean complete;

        RoundCheckpoint(String roomId, int round, int totalAssignments, int doneAssignments,
                        int blockedAssignments, int pendingAssignments, int runningAssignments,
                        boolean complete) {
            this.roomId = roomId; this.round = round; this.totalAssignments = totalAssignments;
            this.doneAssignments = doneAssignments; this.blockedAssignments = blockedAssignments;
            this.pendingAssignments = pendingAssignments; this.runningAssignments = runningAssignments;
            this.complete = complete;
        }
    }

    private final MissionRoom room;

    MissionCoordinator(MissionRoom room) {
        if (room == null) throw new IllegalArgumentException("room");
        this.room = room;
    }

    RoundCheckpoint checkpoint(int round) {
        if (round < 1) throw new IllegalArgumentException("round");
        return new RoundCheckpoint(room.getRoomId(), round, room.countForRound(round),
                room.doneCount(round), room.blockedCount(round), room.pendingCount(round),
                room.runningCount(round), room.isRoundComplete(round));
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