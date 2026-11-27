package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * In-memory registry of logical agents. It deliberately does not create provider
 * accounts, WebViews, credentials, or network connections.
 */
final class AgentRoster {
    enum Status { OFFLINE, READY, BUSY, BLOCKED }

    static final class Agent {
        final String aiId;
        final String displayName;
        final String specialty;
        Status status;

        Agent(String aiId, String displayName, String specialty, Status status) {
            this.aiId = aiId;
            this.displayName = displayName;
            this.specialty = specialty;
            this.status = status;
        }
    }

    private final List<Agent> agents = new ArrayList<>();

    List<Agent> all() {
        return Collections.unmodifiableList(agents);
    }

    Agent find(String aiId) {
        for (Agent agent : agents) if (agent.aiId.equals(aiId)) return agent;
        return null;
    }

    boolean register(String aiId, String displayName, String specialty) {
        if (!AgentRosterPolicy.isValidId(aiId)
                || blank(displayName)
                || blank(specialty)
                || find(aiId) != null
                || !AgentRosterPolicy.canRegister(agents.size())) {
            return false;
        }
        agents.add(new Agent(aiId, displayName.trim(), specialty.trim(), Status.OFFLINE));
        return true;
    }

    boolean setStatus(String aiId, Status status) {
        Agent agent = find(aiId);
        if (agent == null || status == null) return false;
        agent.status = status;
        return true;
    }

    boolean remove(String aiId) {
        Agent agent = find(aiId);
        return agent != null && agents.remove(agent);
    }

    private static boolean blank(String value) {
        return value == null || value.trim().isEmpty();
    }
}
