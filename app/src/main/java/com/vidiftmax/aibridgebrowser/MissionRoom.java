package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Browser-side model for one shared room of individual AI assignments. */
final class MissionRoom {
    private final String roomId;
    private final List<MissionAssignment> assignments = new ArrayList<>();

    MissionRoom(String roomId) {
        if (roomId == null || roomId.trim().isEmpty()) {
            throw new IllegalArgumentException("roomId");
        }
        this.roomId = roomId;
    }

    String getRoomId() {
        return roomId;
    }

    List<MissionAssignment> getAssignments() {
        return Collections.unmodifiableList(assignments);
    }

    boolean addAssignment(MissionAssignment assignment) {
        if (assignment == null || containsAssignment(assignment)) return false;
        assignments.add(assignment);
        return true;
    }

    int countForRound(int round) {
        int count = 0;
        for (MissionAssignment assignment : assignments) {
            if (assignment.round == round) count++;
        }
        return count;
    }

    int pendingCount(int round) {
        return countByStatus(round, MissionAssignment.Status.PENDING);
    }

    int runningCount(int round) {
        return countByStatus(round, MissionAssignment.Status.RUNNING);
    }

    int blockedCount(int round) {
        return countByStatus(round, MissionAssignment.Status.BLOCKED);
    }

    int doneCount(int round) {
        return countByStatus(round, MissionAssignment.Status.DONE);
    }

    boolean isRoundComplete(int round) {
        int total = countForRound(round);
        return total > 0 && doneCount(round) == total;
    }

    private boolean containsAssignment(MissionAssignment candidate) {
        for (MissionAssignment assignment : assignments) {
            if (assignment.missionId.equals(candidate.missionId)
                    && assignment.aiId.equals(candidate.aiId)
                    && assignment.round == candidate.round) {
                return true;
            }
        }
        return false;
    }

    private int countByStatus(int round, MissionAssignment.Status status) {
        int count = 0;
        for (MissionAssignment assignment : assignments) {
            if (assignment.round == round && assignment.status == status) count++;
        }
        return count;
    }
}
