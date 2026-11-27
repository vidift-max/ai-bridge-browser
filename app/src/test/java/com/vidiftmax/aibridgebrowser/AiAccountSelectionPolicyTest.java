package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import java.util.Arrays;
import java.util.List;
import org.junit.Test;

public final class AiAccountSelectionPolicyTest {
    private final List<String> tabs = Arrays.asList("tab-a", "tab-b", "tab-c");
    private final List<String> profiles = Arrays.asList("profile-a", "profile-b", "profile-c");

    @Test public void acceptsTwoDistinctOpenProfiles() {
        assertTrue(AiAccountSelectionPolicy.isValidSelection(tabs, profiles, 0, 1));
        assertTrue(AiAccountSelectionPolicy.isValidSelection(tabs, profiles, 2, 0));
    }

    @Test public void rejectsSelectingTheSameTabTwice() {
        assertFalse(AiAccountSelectionPolicy.isValidSelection(tabs, profiles, 1, 1));
    }

    @Test public void rejectsOutOfRangeIndexes() {
        assertFalse(AiAccountSelectionPolicy.isValidSelection(tabs, profiles, -1, 1));
        assertFalse(AiAccountSelectionPolicy.isValidSelection(tabs, profiles, 0, 3));
    }

    @Test public void rejectsMissingOrMismatchedLists() {
        assertFalse(AiAccountSelectionPolicy.isValidSelection(null, profiles, 0, 1));
        assertFalse(AiAccountSelectionPolicy.isValidSelection(tabs, null, 0, 1));
        assertFalse(AiAccountSelectionPolicy.isValidSelection(tabs, Arrays.asList("only-one"), 0, 1));
    }

    @Test public void rejectsBlankOrDuplicateIdentities() {
        assertFalse(AiAccountSelectionPolicy.isValidSelection(
                Arrays.asList("tab-a", " "), profiles, 0, 1));
        assertFalse(AiAccountSelectionPolicy.isValidSelection(
                tabs, Arrays.asList("profile-a", "profile-a", "profile-c"), 0, 1));
    }
}
