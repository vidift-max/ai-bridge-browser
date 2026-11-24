package com.vidiftmax.aibridgebrowser;

import org.json.JSONObject;
import org.junit.Test;
import static org.junit.Assert.*;

public class FirebaseFirstContactDiagnosticsTest {
    private JSONObject identity() throws Exception {
        return new JSONObject().put("aiId", "AI-01").put("uid", "uid-device-a");
    }
    private JSONObject room() throws Exception {
        return new JSONObject().put("members",
                new JSONObject().put("AI-01", true).put("AI-02", true));
    }

    @Test public void reportsPassWithoutReturningUidOrCredential() throws Exception {
        JSONObject result = FirebaseFirstContactDiagnostics.evaluate(
                "AI-01", "uid-device-a", identity(), room());
        assertEquals("CLIENT_PREFLIGHT_PASS", result.getString("state"));
        assertEquals("PASS", result.getString("roomMembership"));
        assertEquals("NONE", result.getString("credentialDisclosure"));
        assertFalse(result.has("uid"));
        assertFalse(result.has("idToken"));
        assertFalse(result.has("refreshToken"));
    }

    @Test(expected = IllegalStateException.class)
    public void rejectsIdentityMappedToAnotherUid() throws Exception {
        FirebaseFirstContactDiagnostics.evaluate("AI-01", "other-uid", identity(), room());
    }

    @Test(expected = IllegalStateException.class)
    public void rejectsWrongAiIdentity() throws Exception {
        FirebaseFirstContactDiagnostics.evaluate("AI-02", "uid-device-a", identity(), room());
    }

    @Test(expected = IllegalStateException.class)
    public void rejectsMissingRoomMembership() throws Exception {
        FirebaseFirstContactDiagnostics.evaluate("AI-01", "uid-device-a",
                identity(), new JSONObject().put("members", new JSONObject().put("AI-02", true)));
    }

    @Test(expected = IllegalStateException.class)
    public void rejectsMissingConversation() throws Exception {
        FirebaseFirstContactDiagnostics.evaluate("AI-01", "uid-device-a", identity(), null);
    }
}
