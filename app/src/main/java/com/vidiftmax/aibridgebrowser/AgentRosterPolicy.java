package com.vidiftmax.aibridgebrowser;

import java.util.Locale;
import java.util.regex.Pattern;

/** Shared bounds and canonical identity rules for the logical-agent roster. */
final class AgentRosterPolicy {
    static final int MAX_LOGICAL_AGENTS = 20;
    static final int MAX_CONCURRENT_PROVIDER_SESSIONS = 2;

    private static final Pattern CANONICAL_ID = Pattern.compile("AI-(0[1-9]|1[0-9]|20)");

    private AgentRosterPolicy() { }

    static String canonicalId(int ordinal) {
        if (ordinal < 1 || ordinal > MAX_LOGICAL_AGENTS) {
            throw new IllegalArgumentException("agent_ordinal_out_of_range");
        }
        return String.format(Locale.ROOT, "AI-%02d", ordinal);
    }

    static boolean isValidId(String aiId) {
        return aiId != null && CANONICAL_ID.matcher(aiId).matches();
    }

    static boolean canRegister(int currentCount) {
        return currentCount >= 0 && currentCount < MAX_LOGICAL_AGENTS;
    }
}
