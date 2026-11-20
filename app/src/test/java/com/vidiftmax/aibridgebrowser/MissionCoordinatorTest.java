package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class MissionCoordinatorTest {
    @Test public void checkpointAggregatesRoundState() {
        MissionRoom room = new MissionRoom("room-1");
        MissionAssignment a = new MissionAssignment("m1","IA-01",1,10,"mission/1","report/1");
        MissionAssignment b = new MissionAssignment("m2","IA-02",1,10,"mission/2","report/2");
        a.status = MissionAssignment.Status.DONE; b.status = MissionAssignment.Status.RUNNING;
        room.addAssignment(a); room.addAssignment(b);
        MissionCoordinator.RoundCheckpoint c = new MissionCoordinator(room).checkpoint(1);
        assertEquals("room-1", c.roomId); assertEquals(2, c.totalAssignments);
        assertEquals(1, c.doneAssignments); assertEquals(1, c.runningAssignments);
        assertFalse(c.complete);
    }

    @Test public void canAdvanceOnlyWhenEveryAssignmentIsDone() {
        MissionRoom room = new MissionRoom("room-1");
        MissionAssignment a = new MissionAssignment("m1","IA-01",1,10,"mission/1","report/1");
        MissionAssignment b = new MissionAssignment("m2","IA-02",1,10,"mission/2","report/2");
        room.addAssignment(a); room.addAssignment(b);
        MissionCoordinator c = new MissionCoordinator(room);
        assertFalse(c.canAdvance(1)); a.status = MissionAssignment.Status.DONE;
        assertFalse(c.canAdvance(1)); b.status = MissionAssignment.Status.DONE;
        assertTrue(c.canAdvance(1));
    }

    @Test public void incompleteReturnsOnlyUnfinishedAssignments() {
        MissionRoom room = new MissionRoom("room-1");
        MissionAssignment a = new MissionAssignment("m1","IA-01",1,10,"mission/1","report/1");
        MissionAssignment b = new MissionAssignment("m2","IA-02",1,10,"mission/2","report/2");
        a.status = MissionAssignment.Status.DONE; b.status = MissionAssignment.Status.BLOCKED;
        room.addAssignment(a); room.addAssignment(b);
        assertEquals(1, new MissionCoordinator(room).incomplete(1).size());
        assertEquals("IA-02", new MissionCoordinator(room).incomplete(1).get(0).aiId);
    }
}