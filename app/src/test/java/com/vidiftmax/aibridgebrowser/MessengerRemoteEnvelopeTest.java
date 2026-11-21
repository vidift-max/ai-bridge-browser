package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThrows;
import org.junit.Test;

public class MessengerRemoteEnvelopeTest {
    @Test public void acceptsRequiredEnvelopeFields() {
        MessengerRemoteEnvelope e = new MessengerRemoteEnvelope("m1","c1","TEXT","hello");
        assertEquals("m1", e.getMessageId());
        assertEquals("c1", e.getConversationId());
    }

    @Test public void rejectsMissingMessageId() {
        assertThrows(IllegalArgumentException.class,
                () -> new MessengerRemoteEnvelope("", "c1", "TEXT", "hello"));
    }

    @Test public void rejectsMissingBody() {
        assertThrows(IllegalArgumentException.class,
                () -> new MessengerRemoteEnvelope("m1", "c1", "TEXT", ""));
    }
}
