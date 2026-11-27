package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import static org.junit.Assert.*;

public final class DataSafePathPolicyTest {
    @Test public void acceptsRelativeNestedPath() {
        assertEquals("attachments/voice/note.m4a",
                DataSafePathPolicy.validate("attachments/voice/note.m4a"));
    }

    @Test public void rejectsTraversal() {
        assertRejected("../outside.txt");
        assertRejected("browser/../../outside.txt");
        assertRejected("browser/./state.json");
    }

    @Test public void rejectsAbsoluteAndWindowsPaths() {
        assertRejected("/data/private.txt");
        assertRejected("C:/private.txt");
        assertRejected("attachments\\private.txt");
    }

    @Test public void rejectsEmptySegmentsAndControlCharacters() {
        assertRejected("attachments//file");
        assertRejected("attachments/file\nname");
    }

    private static void assertRejected(String path) {
        try {
            DataSafePathPolicy.validate(path);
            fail("Expected rejection for " + path);
        } catch (IllegalArgumentException expected) {
            // Expected fail-closed behavior.
        }
    }
}
