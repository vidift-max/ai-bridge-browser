package com.vidiftmax.aibridgebrowser;

import java.util.HashSet;
import java.util.Set;

final class AiBridgeRoundTripPolicy {
    private static final int MIN_TURNS = 2;
    private static final int MAX_TURNS = 20;

    static boolean isAllowed(String[] aiIds) {
        if (aiIds == null || aiIds.length != 2) return false;
        Set<String> ids = new HashSet<>();
        for (String id : aiIds) if (id != null && !id.trim().isEmpty()) ids.add(id);
        return ids.size() == 2 && ids.contains("AI-01") && ids.contains("AI-02");
    }

    static boolean isTurnCountAllowed(int turns) {
        return turns >= MIN_TURNS && turns <= MAX_TURNS;
    }

    static boolean isFreshResponse(String baseline, String response) {
        return response != null && !response.trim().isEmpty() &&
                !response.equals(baseline == null ? "" : baseline);
    }

    private AiBridgeRoundTripPolicy() {}
}
