package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import static org.junit.Assert.*;

public class CollectiveRoomRemotePolicyTest {
    @Test public void excludesAuthenticatedSenderFromRecipients() {
        List<String> recipients = CollectiveRoomRemotePolicy.recipients(
                Arrays.asList("AI-01", "AI-02", "AI-03"), "AI-01");
        assertEquals(Arrays.asList("AI-02", "AI-03"), recipients);
    }

    @Test public void rejectsMemberListWithoutOwnIdentity() {
        try {
            CollectiveRoomRemotePolicy.recipients(Arrays.asList("AI-02", "AI-03"), "AI-01");
            fail("expected own identity validation");
        } catch (IllegalArgumentException expected) {
            assertEquals("remote_room_own_identity_missing", expected.getMessage());
        }
    }

    @Test public void rejectsDuplicateMembers() {
        try {
            CollectiveRoomRemotePolicy.recipients(Arrays.asList("AI-01", "AI-02", "AI-02"), "AI-01");
            fail("expected duplicate validation");
        } catch (IllegalArgumentException expected) {
            assertEquals("remote_room_duplicate_member", expected.getMessage());
        }
    }

    @Test public void rejectsInvalidIdentity() {
        try {
            CollectiveRoomRemotePolicy.recipients(Arrays.asList("AI-01", "not-an-ai"), "AI-01");
            fail("expected AI_ID validation");
        } catch (IllegalArgumentException expected) {
            assertEquals("invalid_ai_id", expected.getMessage());
        }
    }

    @Test public void recognizesAlreadyPersistedRemoteMessage() {
        assertTrue(CollectiveRoomRemotePolicy.hasSeen(new HashSet<>(Arrays.asList("msg-1")), "msg-1"));
        assertFalse(CollectiveRoomRemotePolicy.hasSeen(new HashSet<>(Arrays.asList("msg-1")), "msg-2"));
    }
}
