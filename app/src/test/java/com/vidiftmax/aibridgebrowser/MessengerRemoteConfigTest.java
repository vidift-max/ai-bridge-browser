package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;
import org.junit.Test;
import java.util.Set;

public class MessengerRemoteConfigTest {
    @Test public void acceptsHttpsAndRemovesTrailingSlash() {
        assertEquals("https://messenger.example", MessengerRemoteConfig.normalizeBaseUrl("https://messenger.example///"));
    }
    @Test public void rejectsInsecureOrCredentialBearingUrls() {
        assertThrows(IllegalArgumentException.class, () -> MessengerRemoteConfig.normalizeBaseUrl("http://messenger.example"));
        assertThrows(IllegalArgumentException.class, () -> MessengerRemoteConfig.normalizeBaseUrl("https://user:pass@messenger.example"));
    }
    @Test public void parsesUniqueMemberIdsAndIncludesCurrentAi() {
        Set<String> ids = MessengerRemoteConfig.parseMemberIds("AI-CLAUDE, AI-GEMINI, AI-CLAUDE", "AI-GPT6");
        assertEquals(3, ids.size());
        assertTrue(ids.contains("AI-GPT6"));
    }
    @Test public void rejectsEmptyMemberTokensAndInvalidCurrentIdentity() {
        assertThrows(IllegalArgumentException.class,
                () -> MessengerRemoteConfig.parseMemberIds("AI-CLAUDE,,AI-GEMINI", "AI-GPT6"));
        assertThrows(IllegalArgumentException.class,
                () -> MessengerRemoteConfig.parseMemberIds("AI-CLAUDE", "not-an-ai"));
    }
    @Test public void rejectsMalformedAndOversizedMembership() {
        assertThrows(IllegalArgumentException.class, () -> MessengerRemoteConfig.parseMemberIds("bad", "AI-GPT6"));
        StringBuilder members = new StringBuilder();
        for (int i=1;i<=20;i++) { if (i>1) members.append(","); members.append("AI-").append(i); }
        assertThrows(IllegalArgumentException.class, () -> MessengerRemoteConfig.parseMemberIds(members.toString(), "AI-GPT6"));
    }
}
