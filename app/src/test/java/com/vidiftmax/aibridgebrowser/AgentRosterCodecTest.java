package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class AgentRosterCodecTest {
    @Test public void roundTripsRosterAndStatuses() {
        AgentRoster roster = new AgentRoster();
        assertTrue(roster.register("AI-01", "Coordinator", "coordination"));
        assertTrue(roster.register("AI-02", "Reviewer", "verification"));
        assertTrue(roster.setStatus("AI-01", AgentRoster.Status.READY));
        AgentRoster restored = AgentRosterCodec.decode(AgentRosterCodec.encode(roster));
        assertEquals(2, restored.size());
        assertEquals("Coordinator", restored.get("AI-01").displayName);
        assertEquals(AgentRoster.Status.READY, restored.get("AI-01").status);
    }

    @Test public void rejectsUnknownSchemaAndDuplicateIdentity() {
        assertThrows(IllegalArgumentException.class,
                () -> AgentRosterCodec.decode("{\"schemaVersion\":2,\"agents\":[]}"));
        assertThrows(IllegalArgumentException.class,
                () -> AgentRosterCodec.decode("{\"schemaVersion\":1,\"agents\":["
                        + "{\"aiId\":\"AI-01\",\"displayName\":\"A\",\"specialty\":\"x\",\"status\":\"OFFLINE\"},"
                        + "{\"aiId\":\"AI-01\",\"displayName\":\"B\",\"specialty\":\"y\",\"status\":\"OFFLINE\"}]}"));
    }

    @Test public void rejectsOutOfScopeBusyAgentAndMalformedJson() {
        assertThrows(IllegalArgumentException.class,
                () -> AgentRosterCodec.decode("{\"schemaVersion\":1,\"agents\":["
                        + "{\"aiId\":\"AI-03\",\"displayName\":\"C\",\"specialty\":\"x\",\"status\":\"BUSY\"}]}"));
        assertThrows(IllegalArgumentException.class, () -> AgentRosterCodec.decode("{"));
    }
}
