package com.vidiftmax.aibridgebrowser;

/** Fail-closed rules for account assignment and tab-bound pending work. */
final class SessionIsolationPolicy {
    private SessionIsolationPolicy() { }

    static boolean canAssignAccount(boolean multiProfileAssigned) {
        return multiProfileAssigned;
    }

    static boolean isQueueTargetCurrent(String targetTabId, String targetProfileId,
                                        String currentTabId, String currentProfileId) {
        return nonBlank(targetTabId) && nonBlank(targetProfileId)
                && targetTabId.equals(currentTabId)
                && targetProfileId.equals(currentProfileId);
    }

    private static boolean nonBlank(String value) {
        return value != null && !value.trim().isEmpty();
    }
}