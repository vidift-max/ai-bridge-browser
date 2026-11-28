package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;
import org.junit.Test;
import org.json.JSONArray;
import org.json.JSONObject;
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
    @Test public void clientRejectsPrivateRoomWithWrongMemberCountBeforeNetwork() throws Exception {
        MessengerHttpClient client = new MessengerHttpClient("https://messenger.example", "AI-GPT6", "test-token");
        JSONArray members = new JSONArray().put("AI-GPT6").put("AI-CLAUDE").put("AI-GEMINI");
        assertThrows(IllegalArgumentException.class, () -> client.createConversation("room-1", members, "PRIVATE"));
    }
    @Test public void clientRejectsEmptyMessageBeforeNetwork() throws Exception {
        MessengerHttpClient client = new MessengerHttpClient("https://messenger.example", "AI-GPT6", "test-token");
        JSONArray recipients = new JSONArray().put("AI-CLAUDE");
        assertThrows(IllegalArgumentException.class, () -> client.sendMessage("room-1", recipients, " "));
    }
    @Test public void toolInvocationEnvelopeHasRequestIdAndNoCallerSuppliedIdentity() throws Exception {
        JSONObject input = new JSONObject().put("duration", "3m");
        JSONObject request = MessengerHttpClient.buildToolInvocationRequest("1.0.0", input);
        assertTrue(request.getString("requestId").matches(
                "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}"));
        assertEquals("1.0.0", request.getString("toolVersion"));
        assertEquals(input.toString(), request.getJSONObject("input").toString());
        assertTrue(!request.has("aiId"));
        assertTrue(!request.has("principalAiId"));
    }

    @Test public void toolInvocationRejectsUnknownToolsAndInvalidVersionsBeforeNetwork() throws Exception {
        MessengerHttpClient client = new MessengerHttpClient("https://messenger.example", "AI-GPT6", "test-token");
        JSONObject input = new JSONObject().put("duration", "3m");
        assertThrows(IllegalArgumentException.class, () -> client.invokeTool("shell_exec", "1.0.0", input));
        assertThrows(IllegalArgumentException.class, () -> client.invokeTool("duration_timer", "1.0", input));
    }

    @Test public void acceptsMinimalValidAiId() {
        assertEquals("AI-1", MessengerRemoteConfig.validateAiId("AI-1"));
    }
    @Test public void rejectsMalformedAndOversizedMembership() {
        assertThrows(IllegalArgumentException.class, () -> MessengerRemoteConfig.parseMemberIds("bad", "AI-GPT6"));
        StringBuilder members = new StringBuilder();
        for (int i=1;i<=20;i++) { if (i>1) members.append(","); members.append("AI-").append(i); }
        assertThrows(IllegalArgumentException.class, () -> MessengerRemoteConfig.parseMemberIds(members.toString(), "AI-GPT6"));
    }
}
