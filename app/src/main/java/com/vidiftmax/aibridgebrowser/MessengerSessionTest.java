package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThrows;
import org.junit.Test;

public class MessengerSessionTest {
    @Test public void storesAuthenticatedIdentityShape() {
        MessengerSession s = new MessengerSession("sess-1", "ai-1", "provider-subject-1");
        assertEquals("ai-1", s.getAiId());
        assertEquals("provider-subject-1", s.getProviderSubject());
    }

    @Test public void rejectsMissingIdentity() {
        assertThrows(IllegalArgumentException.class,
                () -> new MessengerSession("sess-1", "", "provider-subject-1"));
    }
}
