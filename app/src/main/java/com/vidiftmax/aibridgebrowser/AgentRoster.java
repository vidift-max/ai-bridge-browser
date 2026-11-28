package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Logical agent registry. Registration does not create provider accounts or sessions. */
final class AgentRoster {
    enum Status { OFFLINE, READY, BUSY, PAUSED }

    static final class Agent {
        final String aiId;
        final String displayName;
        final String specialty;
        final Status status;

        Agent(String aiId, String displayName, String specialty, Status status) {
            this.aiId = aiId;
            this.displayName = displayName;
            this.specialty = specialty;
            this.status = status;
        }
    }

    private final Map<String, Agent> agents = new LinkedHashMap<>();

    synchronized boolean register(String aiId, String displayName, String specialty) {
        if (!AgentRosterPolicy.isValidId(aiId) || blank(displayName) || blank(specialty)
                || agents.containsKey(aiId) || !AgentRosterPolicy.canRegister(agents.size())) {
            return false;
        }
        agents.put(aiId, new Agent(aiId, displayName.trim(), specialty.trim(), Status.OFFLINE));
        return true;
    }

    synchronized boolean setStatus(String aiId, Status status) {
        Agent current = agents.get(aiId);
        if (current == null || status == null) return false;
        if (status == Status.BUSY) {
            if (!AgentRosterPolicy.isProviderSessionAllowedForCurrentMission(aiId)) return false;
            int busy = 0;
            for (Agent agent : agents.values()) if (agent.status == Status.BUSY) busy++;
            if (current.status != Status.BUSY && !AgentRosterPolicy.canOpenProviderSession(busy)) return false;
        }
        agents.put(aiId, new Agent(current.aiId, current.displayName, current.specialty, status));
        return true;
    }

    synchronized boolean remove(String aiId) {
        Agent current = agents.get(aiId);
        if (current == null || current.status == Status.BUSY) return false;
        agents.remove(aiId);
        return true;
    }

    synchronized Agent get(String aiId) { return agents.get(aiId); }

    synchronized List<Agent> all() {
        return Collections.unmodifiableList(new ArrayList<>(agents.values()));
    }

    synchronized int size() { return agents.size(); }

    synchronized int busyCount() {
        int count = 0;
        for (Agent agent : agents.values()) if (agent.status == Status.BUSY) count++;
        return count;
    }

    synchronized void replaceAll(List<Agent> restored) {
        if (restored == null || restored.size() > AgentRosterPolicy.MAX_LOGICAL_AGENTS)
            throw new IllegalArgumentException("invalid_roster");
        Map<String, Agent> candidate = new LinkedHashMap<>();
        int busy = 0;
        for (Agent agent : restored) {
            if (agent == null || !AgentRosterPolicy.isValidId(agent.aiId)
                    || blank(agent.displayName) || blank(agent.specialty) || agent.status == null
                    || candidate.containsKey(agent.aiId)) throw new IllegalArgumentException("invalid_roster");
            if (agent.status == Status.BUSY) {
                if (!AgentRosterPolicy.isProviderSessionAllowedForCurrentMission(agent.aiId))
                    throw new IllegalArgumentException("agent_session_out_of_scope");
                busy++;
            }
            candidate.put(agent.aiId, agent);
        }
        if (busy > AgentRosterPolicy.MAX_CONCURRENT_PROVIDER_SESSIONS)
            throw new IllegalArgumentException("provider_session_limit");
        agents.clear();
        agents.putAll(candidate);
    }

    private static boolean blank(String value) { return value == null || value.trim().isEmpty(); }
}
