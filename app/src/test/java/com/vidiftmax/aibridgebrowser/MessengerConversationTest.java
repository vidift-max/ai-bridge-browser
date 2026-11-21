package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class MessengerConversationTest {
    @Test public void createsDistinctLocalConversationIds() {
        MessengerConversation first = new MessengerConversation("Equipe - planejamento", 1760000000000L);
        MessengerConversation second = new MessengerConversation("Equipe - planejamento", 1760000000001L);
        assertNotEquals(first.getConversationId(), second.getConversationId());
        assertEquals("Equipe - planejamento", first.getTitle());
        assertEquals(MessengerConversation.KIND_LOCAL_SANDBOX, first.getKind());
        assertEquals(MessengerConversation.STATUS_LOCAL_ONLY, first.getStatus());
    }

    @Test public void rejectsInvalidConversationTitleAndTimestamp() {
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerConversation(" ", 1760000000000L));
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerConversation("x".repeat(61), 1760000000000L));
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerConversation("Projeto", 0));
    }
}
