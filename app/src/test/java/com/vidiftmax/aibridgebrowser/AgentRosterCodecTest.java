package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class AgentRosterCodecTest {
    @Test public void roundTripsRosterAndStatuses() throws Exception {
        AgentRoster source = new AgentRoster();
        assertTrue(source.register("AI-01", "Coordinator", "Coordination"));
        assertTrue(source.register("AI-02", "Research", "Research"));
        assertTrue(source.setStatus("AI-02", AgentRoster.Status.READY));

        AgentRoster restored = AgentRosterCodec.decode(AgentRosterCodec.encode(source));
        assertEquals(2, restored.all().size());
        assertEquals("Coordinator", restored.find("AI-01").displayName);
        assertEquals(AgentRoster.Status.OFFLINE, restored.find("AI-01").status);
        assertEquals(AgentRoster.Status.READY, restored.find("AI-02").status);
    }

    @Test public void rejectsUnsupportedSchemaAndMalformedPayload() throws Exception {
        try {
            AgentRosterCodec.decode("{\"schemaVersion\":99,\"agents\":[]}");
            fail("unsupported_schema_must_fail_closed");
        } catch (IllegalArgumentException expected) {
            assertEquals("unsupported_roster_schema", expected.getMessage());
        }
        try {
            AgentRosterCodec.decode("{");
            fail("malformed_json_must_fail");
        } catch (org.json.JSONException expected) {
            assertNotNull(expected);
        }
    }

    @Test public void rejectsDuplicateAndInvalidAgentRecords() throws Exception {
        String duplicate = "{\"schemaVersion\":1,\"agents\":["
                + "{\"aiId\":\"AI-01\",\"displayName\":\"One\",\"specialty\":\"SEO\",\"status\":\"OFFLINE\"},"
                + "{\"aiId\":\"AI-01\",\"displayName\":\"Two\",\"specialty\":\"SEO\",\"status\":\"READY\"}]}";
        try {
            AgentRosterCodec.decode(duplicate);
            fail("duplicate_agent_must_fail");
        } catch (IllegalArgumentException expected) {
            assertEquals("invalid_or_duplicate_agent", expected.getMessage());
        }
    }

    @Test public void rejectsUnknownStatus() throws Exception {
        String invalid = "{\"schemaVersion\":1,\"agents\":["
                + "{\"aiId\":\"AI-01\",\"displayName\":\"One\",\"specialty\":\"SEO\",\"status\":\"MAGIC\"}]}";
        try {
            AgentRosterCodec.decode(invalid);
            fail("unknown_status_must_fail");
        } catch (IllegalArgumentException expected) {
            assertEquals("invalid_agent_status", expected.getMessage());
        }
    }
}
