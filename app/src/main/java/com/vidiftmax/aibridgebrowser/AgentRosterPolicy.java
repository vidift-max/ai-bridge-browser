package com.vidiftmax.aibridgebrowser;

/**
 * Product-level roster policy. Logical agents are not browser tabs or provider accounts.
 * The current provider-session mission remains limited to AI-01 and AI-02.
 */
final class AgentRosterPolicy {
    static final int MAX_LOGICAL_AGENTS = 20;
    static final int MAX_CONCURRENT_PROVIDER_SESSIONS = 2;

    private AgentRosterPolicy() { }

    static String canonicalId(int ordinal) {
        if (ordinal < 1 || ordinal > MAX_LOGICAL_AGENTS) {
            throw new IllegalArgumentException("agent_ordinal_out_of_range");
        }
        return String.format(java.util.Locale.ROOT, "AI-%02d", ordinal);
    }

    static boolean isValidId(String aiId) {
        if (aiId == null || !aiId.matches("AI-[0-9]{2}")) return false;
        try {
            int ordinal = Integer.parseInt(aiId.substring(3));
            return ordinal >= 1 && ordinal <= MAX_LOGICAL_AGENTS
                    && canonicalId(ordinal).equals(aiId);
        } catch (RuntimeException ignored) {
            return false;
        }
    }

    static boolean canRegister(int currentCount) {
        return currentCount >= 0 && currentCount < MAX_LOGICAL_AGENTS;
    }

    static boolean canOpenProviderSession(int activeSessions) {
        return activeSessions >= 0
                && activeSessions < MAX_CONCURRENT_PROVIDER_SESSIONS;
    }

    static boolean isProviderSessionAllowedForCurrentMission(String aiId) {
        return "AI-01".equals(aiId) || "AI-02".equals(aiId);
    }
}
