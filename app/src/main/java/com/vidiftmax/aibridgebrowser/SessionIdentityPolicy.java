package com.vidiftmax.aibridgebrowser;

import java.util.List;

/** Guards restored WebView identities against duplicate tab or cookie/storage profiles. */
final class SessionIdentityPolicy {
    private SessionIdentityPolicy() { }

    static boolean isUnique(String candidate, List<String> existing) {
        if (candidate == null || candidate.trim().isEmpty() || existing == null) return false;
        return !existing.contains(candidate);
    }
}
