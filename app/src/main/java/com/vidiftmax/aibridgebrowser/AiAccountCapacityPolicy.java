package com.vidiftmax.aibridgebrowser;

/** Separates the product ceiling from the deliberately smaller active mission scope. */
final class AiAccountCapacityPolicy {
    static final int MAX_SUPPORTED_ACCOUNTS = 20;
    static final int CURRENT_MISSION_LIMIT = 2;

    private AiAccountCapacityPolicy() { }

    static boolean canActivate(int activeCount) {
        return activeCount >= 0 && activeCount < CURRENT_MISSION_LIMIT;
    }

    static boolean supportsAccountCount(int requestedCount) {
        return requestedCount >= 1 && requestedCount <= MAX_SUPPORTED_ACCOUNTS;
    }
}
