package com.vidiftmax.aibridgebrowser;

import java.util.List;

/** Validates explicit mapping of two already-open, isolated browser profiles to AI-01 and AI-02. */
final class AiAccountSelectionPolicy {
    private AiAccountSelectionPolicy() { }

    static boolean isValidSelection(List<String> tabIds, List<String> profileIds,
                                    int ai01Index, int ai02Index) {
        if (tabIds == null || profileIds == null || tabIds.size() != profileIds.size()
                || ai01Index < 0 || ai02Index < 0
                || ai01Index >= tabIds.size() || ai02Index >= tabIds.size()
                || ai01Index == ai02Index) return false;
        String tab01 = tabIds.get(ai01Index);
        String tab02 = tabIds.get(ai02Index);
        String profile01 = profileIds.get(ai01Index);
        String profile02 = profileIds.get(ai02Index);
        return nonBlank(tab01) && nonBlank(tab02) && nonBlank(profile01) && nonBlank(profile02)
                && !tab01.equals(tab02) && !profile01.equals(profile02);
    }

    private static boolean nonBlank(String value) {
        return value != null && !value.trim().isEmpty();
    }
}
