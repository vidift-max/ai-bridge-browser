package com.vidiftmax.aibridgebrowser;

/** Fail-closed launch gate for the user-started AI-01 / AI-02 first contact. */
final class AiConversationLaunchPolicy {
    private AiConversationLaunchPolicy() { }

    static String blockingReason(boolean hasAi01, boolean hasAi02,
                                 boolean distinctTabs, boolean distinctProfiles,
                                 boolean profilesVerified, boolean pagesReady,
                                 boolean chatHostsReady) {
        if (!hasAi01 || !hasAi02) return "AI_IDENTITIES_NOT_ASSIGNED";
        if (!distinctTabs) return "TABS_NOT_DISTINCT";
        if (!distinctProfiles) return "PROFILES_NOT_DISTINCT";
        if (!profilesVerified) return "PROFILE_ISOLATION_UNVERIFIED";
        if (!pagesReady) return "PAGES_NOT_READY";
        if (!chatHostsReady) return "CHATGPT_NOT_OPEN";
        return null;
    }
}
