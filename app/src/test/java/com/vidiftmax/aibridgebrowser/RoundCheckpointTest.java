package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import java.util.Arrays;
import org.junit.Test;

public class RoundCheckpointTest {
    @Test public void aggregatesEntriesWithoutExposingMutableList() {
        RoundCheckpoint.Entry a = new RoundCheckpoint.Entry("IA-01","m1","DONE","report/1");
        RoundCheckpoint.Entry b = new RoundCheckpoint.Entry("IA-02","m2","BLOCKED","report/2");
        RoundCheckpoint c = new RoundCheckpoint("room-1",1,10,Arrays.asList(a,b));
        assertEquals("1/10", c.roundLabel());
        assertEquals(1, c.doneCount());
        assertEquals(1, c.blockedCount());
        assertFalse(c.complete());
        try {
            c.entries.add(a);
            fail("entries must be immutable");
        } catch (UnsupportedOperationException expected) {
            // expected
        }
    }

    @Test public void completeRequiresAllEntriesDone() {
        RoundCheckpoint.Entry a = new RoundCheckpoint.Entry("IA-01","m1","DONE","report/1");
        RoundCheckpoint.Entry b = new RoundCheckpoint.Entry("IA-02","m2","DONE","report/2");
        assertTrue(new RoundCheckpoint("room-1",2,10,Arrays.asList(a,b)).complete());
    }
}