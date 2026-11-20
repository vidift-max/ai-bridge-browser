package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class MissionRoomTest {
    private MissionAssignment assignment(String missionId, String aiId, int round) {
        return new MissionAssignment(
                missionId, aiId, round, 10,
                "https://example.invalid/mission/" + missionId,
                "https://example.invalid/report/" + aiId);
    }

    @Test public void acceptsDifferentAssignmentsAndCountsStatuses() {
        MissionRoom room = new MissionRoom("room-01");
        MissionAssignment a = assignment("m-01", "IA-01", 1);
        MissionAssignment b = assignment("m-02", "IA-02", 1);
        assertTrue(room.addAssignment(a));
        assertTrue(room.addAssignment(b));
        assertEquals(2, room.countForRound(1));
        assertEquals(2, room.pendingCount(1));
        assertFalse(room.isRoundComplete(1));

        a.status = MissionAssignment.Status.DONE;
        b.status = MissionAssignment.Status.RUNNING;
        assertEquals(1, room.doneCount(1));
        assertEquals(1, room.runningCount(1));
    }

    @Test public void rejectsDuplicateMissionAiRound() {
        MissionRoom room = new MissionRoom("room-01");
        assertTrue(room.addAssignment(assignment("m-01", "IA-01", 1)));
        assertFalse(room.addAssignment(assignment("m-01", "IA-01", 1)));
        assertEquals(1, room.getAssignments().size());
    }

    @Test public void roundCompletesOnlyWhenEveryAssignmentIsDone() {
        MissionRoom room = new MissionRoom("room-01");
        MissionAssignment a = assignment("m-01", "IA-01", 1);
        MissionAssignment b = assignment("m-02", "IA-02", 1);
        room.addAssignment(a);
        room.addAssignment(b);

        a.status = MissionAssignment.Status.DONE;
        assertFalse(room.isRoundComplete(1));

        b.status = MissionAssignment.Status.DONE;
        assertTrue(room.isRoundComplete(1));
        assertFalse(room.isRoundComplete(2));
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsBlankRoomId() {
        new MissionRoom(" ");
    }
}
