package com.vidiftmax.aibridgebrowser;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/** Versioned JSON codec for saving the logical roster in Android private app storage. */
final class AgentRosterCodec {
    private static final int SCHEMA_VERSION = 1;

    private AgentRosterCodec() { }

    static String encode(AgentRoster roster) throws JSONException {
        if (roster == null) throw new IllegalArgumentException("roster_required");
        JSONObject root = new JSONObject();
        root.put("schemaVersion", SCHEMA_VERSION);
        JSONArray items = new JSONArray();
        for (AgentRoster.Agent agent : roster.all()) {
            JSONObject item = new JSONObject();
            item.put("aiId", agent.aiId);
            item.put("displayName", agent.displayName);
            item.put("specialty", agent.specialty);
            item.put("status", agent.status.name());
            items.put(item);
        }
        root.put("agents", items);
        return root.toString();
    }

    static AgentRoster decode(String encoded) throws JSONException {
        if (encoded == null || encoded.trim().isEmpty()) {
            throw new IllegalArgumentException("roster_json_required");
        }
        JSONObject root = new JSONObject(encoded);
        if (root.optInt("schemaVersion", -1) != SCHEMA_VERSION) {
            throw new IllegalArgumentException("unsupported_roster_schema");
        }
        JSONArray items = root.optJSONArray("agents");
        if (items == null || items.length() > AgentRosterPolicy.MAX_LOGICAL_AGENTS) {
            throw new IllegalArgumentException("invalid_roster_items");
        }
        AgentRoster roster = new AgentRoster();
        for (int i = 0; i < items.length(); i++) {
            JSONObject item = items.optJSONObject(i);
            if (item == null) throw new IllegalArgumentException("invalid_agent_record");
            String aiId = item.optString("aiId", "");
            String name = item.optString("displayName", "");
            String specialty = item.optString("specialty", "");
            String rawStatus = item.optString("status", AgentRoster.Status.OFFLINE.name());
            if (!roster.register(aiId, name, specialty)) {
                throw new IllegalArgumentException("invalid_or_duplicate_agent");
            }
            AgentRoster.Status status;
            try {
                status = AgentRoster.Status.valueOf(rawStatus);
            } catch (RuntimeException invalidStatus) {
                throw new IllegalArgumentException("invalid_agent_status");
            }
            if (!roster.setStatus(aiId, status)) {
                throw new IllegalArgumentException("agent_restore_failed");
            }
        }
        return roster;
    }
}
