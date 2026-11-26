package com.vidiftmax.aibridgebrowser;

import java.util.Collection;

/** Guards logical WebView profile identity; this does not prove provider-level data isolation. */
public final class SessionProfilePolicy {
    private SessionProfilePolicy() { }

    public static boolean hasUniqueProfileId(String profileId, Collection<String> assignedProfileIds) {
        if (profileId == null || profileId.trim().isEmpty()) return false;
        if (assignedProfileIds == null) return true;
        for (String assigned : assignedProfileIds) {
            if (profileId.equals(assigned)) return false;
        }
        return true;
    }

    public static boolean canClaimProfileIsolation(boolean featureSupported,
                                                    boolean assignmentSucceeded,
                                                    boolean uniqueProfileId) {
        return featureSupported && assignmentSucceeded && uniqueProfileId;
    }
}
