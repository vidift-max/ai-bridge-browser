package com.vidiftmax.aibridgebrowser;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;

/** Strict, versioned JSON codec for local logical-agent roster snapshots. */
final class AgentRosterCodec {
    static final int SCHEMA_VERSION = 1;
    private AgentRosterCodec() { }

    static String encode(AgentRoster roster) {
        if (roster == null) throw new IllegalArgumentException("roster_required");
        try {
            JSONArray agents = new JSONArray();
            for (AgentRoster.Agent agent : roster.all()) {
                JSONObject item = new JSONObject();
                item.put("aiId", agent.aiId);
                item.put("displayName", agent.displayName);
                item.put("specialty", agent.specialty);
                item.put("status", agent.status.name());
                agents.put(item);
            }
            JSONObject root = new JSONObject();
            root.put("schemaVersion", SCHEMA_VERSION);
            root.put("agents", agents);
            return root.toString();
        } catch (JSONException error) {
            throw new IllegalArgumentException("roster_encode_failed", error);
        }
    }

    static AgentRoster decode(String encoded) {
        if (encoded == null || encoded.trim().isEmpty()) throw new IllegalArgumentException("roster_snapshot_required");
        try {
            JSONObject root = new JSONObject(encoded);
            if (root.optInt("schemaVersion", -1) != SCHEMA_VERSION)
                throw new IllegalArgumentException("unsupported_roster_schema");
            JSONArray items = root.getJSONArray("agents");
            if (items.length() > AgentRosterPolicy.MAX_LOGICAL_AGENTS)
                throw new IllegalArgumentException("roster_capacity_exceeded");
            List<AgentRoster.Agent> restored = new ArrayList<>();
            for (int i = 0; i < items.length(); i++) {
                JSONObject item = items.getJSONObject(i);
                String aiId = item.getString("aiId");
                String name = item.getString("displayName");
                String specialty = item.getString("specialty");
                AgentRoster.Status status;
                try { status = AgentRoster.Status.valueOf(item.getString("status")); }
                catch (RuntimeException invalid) { throw new IllegalArgumentException("invalid_agent_status", invalid); }
                restored.add(new AgentRoster.Agent(aiId, name, specialty, status));
            }
            AgentRoster roster = new AgentRoster();
            roster.replaceAll(restored);
            return roster;
        } catch (JSONException error) {
            throw new IllegalArgumentException("invalid_roster_snapshot", error);
        }
    }
}
