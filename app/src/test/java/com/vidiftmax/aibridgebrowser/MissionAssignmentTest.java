package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class MissionAssignmentTest {
    @Test public void keepsIndividualAiMissionAndRound() {
        MissionAssignment assignment = new MissionAssignment(
                "mission-154-ia07", "IA-07", 4, 10,
                "https://github.com/vidift-max/ai-bridge-browser/blob/v2-saas-alpha/missions/154/IA-07.md",
                "https://github.com/vidift-max/ai-bridge-browser/blob/v2-saas-alpha/missions/154/reports/IA-07.md");

        assertEquals("IA-07", assignment.aiId);
        assertEquals("4/10", assignment.roundLabel());
        assertEquals(MissionAssignment.Status.PENDING, assignment.status);
        assertFalse(assignment.isComplete());
    }

    @Test public void statusCanMoveToDoneWithoutChangingIdentity() {
        MissionAssignment assignment = new MissionAssignment(
                "mission-154-ia01", "IA-01", 1, 3, "mission://01", "report://01");
        assignment.status = MissionAssignment.Status.DONE;
        assertTrue(assignment.isComplete());
        assertEquals("mission-154-ia01", assignment.missionId);
        assertEquals("mission://01", assignment.missionUrl);
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsRoundOutsideTotal() {
        new MissionAssignment("m", "IA-01", 4, 3, "mission://01", "");
    }
}
