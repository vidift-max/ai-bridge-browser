package com.vidiftmax.aibridgebrowser;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/**
 * Privacy-preserving in-memory evidence for one user-started AI-01 <-> AI-02 run.
 * Response bodies are never retained; only length, SHA-256 and capture time are stored.
 */
final class AiBridgeEvidence {
    static final int MAX_EVENTS = 20;

    static final class Event {
        final int turn;
        final String senderAiId;
        final int responseChars;
        final String responseSha256;
        final long capturedAtEpochMs;

        Event(int turn, String senderAiId, int responseChars,
              String responseSha256, long capturedAtEpochMs) {
            this.turn = turn;
            this.senderAiId = senderAiId;
            this.responseChars = responseChars;
            this.responseSha256 = responseSha256;
            this.capturedAtEpochMs = capturedAtEpochMs;
        }
    }

    private final List<Event> events = new ArrayList<>();

    void clear() {
        events.clear();
    }

    boolean addTurn(int turn, String senderAiId, String response) {
        if (turn != events.size() + 1 || turn < 1 || turn > MAX_EVENTS
                || senderAiId == null || response == null || response.trim().isEmpty()) return false;
        String expectedSender = (turn % 2 == 1) ? "AI-01" : "AI-02";
        if (!expectedSender.equals(senderAiId)) return false;
        String digest = sha256(response);
        if (digest == null) return false;
        events.add(new Event(turn, senderAiId, response.length(), digest,
                System.currentTimeMillis()));
        return true;
    }

    int turnCount() {
        return events.size();
    }

    boolean isAlternatingPair() {
        if (events.isEmpty()) return false;
        for (int i = 0; i < events.size(); i++) {
            Event event = events.get(i);
            String expected = (i % 2 == 0) ? "AI-01" : "AI-02";
            if (event.turn != i + 1 || !expected.equals(event.senderAiId)
                    || event.responseChars < 1 || event.responseSha256 == null
                    || event.responseSha256.length() != 64 || event.capturedAtEpochMs <= 0) {
                return false;
            }
        }
        return true;
    }

    List<Event> events() {
        return Collections.unmodifiableList(events);
    }

    String summary() {
        return "turnos=" + turnCount() + " · integridade="
                + (isAlternatingPair() ? "OK" : "PENDENTE");
    }

    private static String sha256(String value) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(value.getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder(64);
            for (byte b : digest) hex.append(String.format(Locale.ROOT, "%02x", b & 0xff));
            return hex.toString();
        } catch (Exception ignored) {
            return null;
        }
    }
}