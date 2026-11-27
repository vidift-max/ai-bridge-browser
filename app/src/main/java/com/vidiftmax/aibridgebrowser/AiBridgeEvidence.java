package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** In-memory evidence for one user-started AI-01 <-> AI-02 roundtrip. */
final class AiBridgeEvidence {
    static final int MAX_EVENTS = 40;

    static final class Event {
        final int turn;
        final String senderAiId;
        final int responseChars;

        Event(int turn, String senderAiId, int responseChars) {
            this.turn = turn;
            this.senderAiId = senderAiId;
            this.responseChars = responseChars;
        }
    }

    private final List<Event> events = new ArrayList<>();

    void clear() {
        events.clear();
    }

    boolean addTurn(int turn, String senderAiId, String response) {
        if (turn < 1 || senderAiId == null || senderAiId.trim().isEmpty()
                || response == null || response.trim().isEmpty()
                || events.size() >= MAX_EVENTS) return false;
        events.add(new Event(turn, senderAiId, response.length()));
        return true;
    }

    int turnCount() {
        return events.size();
    }

    boolean isAlternatingPair() {
        if (events.size() < 2) return false;
        for (int i = 0; i < events.size(); i++) {
            String expected = (i % 2 == 0) ? "AI-01" : "AI-02";
            if (!expected.equals(events.get(i).senderAiId)) return false;
        }
        return true;
    }

    List<Event> events() {
        return Collections.unmodifiableList(events);
    }

    String summary() {
        return "turnos=" + turnCount() + " · alternância="
                + (isAlternatingPair() ? "OK" : "PENDENTE");
    }
}
