package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** In-process FIFO mission scheduler; only AI-01/AI-02 may claim provider sessions today. */
final class AgentMissionQueue {
    enum State { QUEUED, RUNNING, COMPLETED, CANCELLED }

    static final class Mission {
        final String missionId;
        final String aiId;
        final String instruction;
        State state;

        Mission(String missionId, String aiId, String instruction) {
            this.missionId = missionId;
            this.aiId = aiId;
            this.instruction = instruction;
            this.state = State.QUEUED;
        }
    }

    private static final int MAX_INSTRUCTION_LENGTH = 5000;
    private final List<Mission> missions = new ArrayList<>();

    synchronized boolean enqueue(String missionId, String aiId, String instruction) {
        if (blank(missionId) || missionId.length() > 200 || !AgentRosterPolicy.isValidId(aiId)
                || blank(instruction) || instruction.length() > MAX_INSTRUCTION_LENGTH
                || find(missionId) != null) return false;
        missions.add(new Mission(missionId.trim(), aiId, instruction.trim()));
        return true;
    }

    synchronized Mission claimNext() {
        if (!AgentRosterPolicy.canOpenProviderSession(activeCount())) return null;
        for (Mission mission : missions) {
            if (mission.state != State.QUEUED
                    || !AgentRosterPolicy.isProviderSessionAllowedForCurrentMission(mission.aiId)
                    || hasRunningMissionFor(mission.aiId)) continue;
            mission.state = State.RUNNING;
            return mission;
        }
        return null;
    }

    synchronized boolean complete(String missionId) {
        Mission mission = find(missionId);
        if (mission == null || mission.state != State.RUNNING) return false;
        mission.state = State.COMPLETED;
        return true;
    }

    synchronized boolean cancel(String missionId) {
        Mission mission = find(missionId);
        if (mission == null || mission.state != State.QUEUED) return false;
        mission.state = State.CANCELLED;
        return true;
    }

    synchronized int activeCount() {
        int count = 0;
        for (Mission mission : missions) if (mission.state == State.RUNNING) count++;
        return count;
    }

    synchronized List<Mission> all() {
        return Collections.unmodifiableList(new ArrayList<>(missions));
    }

    private boolean hasRunningMissionFor(String aiId) {
        for (Mission mission : missions)
            if (mission.aiId.equals(aiId) && mission.state == State.RUNNING) return true;
        return false;
    }

    private Mission find(String missionId) {
        if (missionId == null) return null;
        for (Mission mission : missions) if (mission.missionId.equals(missionId)) return mission;
        return null;
    }

    private static boolean blank(String value) { return value == null || value.trim().isEmpty(); }
}
