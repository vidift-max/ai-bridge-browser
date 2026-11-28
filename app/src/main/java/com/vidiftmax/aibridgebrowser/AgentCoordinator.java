package com.vidiftmax.aibridgebrowser;

import java.util.List;

/** GPT-6 coordination boundary for logical agents and the bounded provider-session queue. */
final class AgentCoordinator {
    static final String COORDINATOR_ID = "GPT-6";

    private final AgentRoster roster;
    private final AgentMissionQueue queue;

    AgentCoordinator() { this(new AgentRoster(), new AgentMissionQueue()); }

    AgentCoordinator(AgentRoster roster, AgentMissionQueue queue) {
        if (roster == null || queue == null) throw new IllegalArgumentException("coordinator_dependencies_required");
        this.roster = roster;
        this.queue = queue;
    }

    String coordinatorId() { return COORDINATOR_ID; }

    boolean registerAgent(String aiId, String displayName, String specialty) {
        return roster.register(aiId, displayName, specialty);
    }

    boolean assignMission(String missionId, String aiId, String instruction) {
        if (roster.get(aiId) == null) return false;
        return queue.enqueue(missionId, aiId, instruction);
    }

    AgentMissionQueue.Mission dispatchNext() {
        AgentMissionQueue.Mission mission = queue.claimNext();
        if (mission == null) return null;
        if (!roster.setStatus(mission.aiId, AgentRoster.Status.BUSY)) {
            queue.complete(mission.missionId);
            return null;
        }
        return mission;
    }

    boolean completeMission(String missionId) {
        AgentMissionQueue.Mission target = null;
        for (AgentMissionQueue.Mission mission : queue.all()) {
            if (mission.missionId.equals(missionId)) { target = mission; break; }
        }
        if (target == null || target.state != AgentMissionQueue.State.RUNNING) return false;
        if (!queue.complete(missionId)) return false;
        roster.setStatus(target.aiId, AgentRoster.Status.READY);
        return true;
    }

    boolean cancelMission(String missionId) { return queue.cancel(missionId); }

    AgentRoster.Agent agent(String aiId) { return roster.get(aiId); }
    List<AgentRoster.Agent> agents() { return roster.all(); }
    List<AgentMissionQueue.Mission> missions() { return queue.all(); }
    int activeProviderSessions() { return queue.activeCount(); }
}
