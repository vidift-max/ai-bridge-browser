package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class MessengerMessageTest {
    @Test public void createsLocalOnlyMessageWithStableId() {
        MessengerMessage message = new MessengerMessage(
                "LOCAL-DEMO", "Este dispositivo", "Olá equipe", 1760000000000L);
        assertNotNull(message.getMessageId());
        assertEquals("LOCAL-DEMO", message.getConversationId());
        assertEquals("Olá equipe", message.getBody());
        assertEquals(MessengerMessage.STATUS_LOCAL_ONLY, message.getStatus());
    }

    @Test public void rejectsEmptyFieldsAndOversizedBody() {
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerMessage("LOCAL-DEMO", "Este dispositivo", " ", 1760000000000L));
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerMessage("", "Este dispositivo", "Olá", 1760000000000L));
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerMessage("LOCAL-DEMO", "Este dispositivo", "Olá", 0));
        assertThrows(IllegalArgumentException.class, () ->
                new MessengerMessage("LOCAL-DEMO", "Este dispositivo", "x".repeat(4001), 1760000000000L));
    }
}
