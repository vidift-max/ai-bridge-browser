package com.vidiftmax.aibridgebrowser;

/** Fail-closed rules for account assignment and tab-bound pending work. */
final class SessionIsolationPolicy {
    private SessionIsolationPolicy() { }

    static boolean canAssignAccount(boolean multiProfileAssigned) {
        return multiProfileAssigned;
    }

    /** A successful setProfile call is not enough: verify WebView reports the requested profile. */
    static boolean isAssignedProfile(String expectedProfileId, String actualProfileId) {
        return nonBlank(expectedProfileId) && expectedProfileId.equals(actualProfileId);
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