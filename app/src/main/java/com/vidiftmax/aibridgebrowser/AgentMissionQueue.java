package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Small in-process FIFO scheduler for logical-agent missions.
 * It does not automate provider UIs or imply that an AI model is connected.
 */
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

    private final List<Mission> missions = new ArrayList<>();

    synchronized List<Mission> all() {
        return Collections.unmodifiableList(new ArrayList<>(missions));
    }

    synchronized boolean enqueue(String missionId, String aiId, String instruction) {
        if (blank(missionId) || !AgentRosterPolicy.isValidId(aiId) || blank(instruction)
                || find(missionId) != null) return false;
        missions.add(new Mission(missionId.trim(), aiId, instruction.trim()));
        return true;
    }

    synchronized Mission claimNext() {
        if (activeCount() >= AgentRosterPolicy.MAX_CONCURRENT_PROVIDER_SESSIONS) return null;
        for (Mission mission : missions) {
            if (mission.state == State.QUEUED) {
                mission.state = State.RUNNING;
                return mission;
            }
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

    private Mission find(String missionId) {
        if (missionId == null) return null;
        for (Mission mission : missions) if (mission.missionId.equals(missionId)) return mission;
        return null;
    }

    private static boolean blank(String value) {
        return value == null || value.trim().isEmpty();
    }
}
