package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class MissionCoordinatorAggregateTest {
    @Test public void buildsOneCheckpointWithEveryAssignedAi() {
        MissionRoom room = new MissionRoom("room-1");
        MissionAssignment a = new MissionAssignment("m1","IA-01",1,10,"mission/1","report/1");
        MissionAssignment b = new MissionAssignment("m2","IA-02",1,10,"mission/2","report/2");
        a.status = MissionAssignment.Status.DONE;
        b.status = MissionAssignment.Status.BLOCKED;
        room.addAssignment(a);
        room.addAssignment(b);

        RoundCheckpoint checkpoint = new MissionCoordinator(room).aggregatedCheckpoint(1);

        assertEquals("room-1", checkpoint.roomId);
        assertEquals("1/10", checkpoint.roundLabel());
        assertEquals(2, checkpoint.entries.size());
        assertEquals(1, checkpoint.doneCount());
        assertEquals(1, checkpoint.blockedCount());
        assertFalse(checkpoint.complete());
        assertEquals("IA-02", checkpoint.entries.get(1).aiId);
        assertEquals("report/2", checkpoint.entries.get(1).reportUrl);
    }
}