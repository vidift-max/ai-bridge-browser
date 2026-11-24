package com.vidiftmax.aibridgebrowser;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import static org.junit.Assert.*;
public class FirebaseMessageAdmissionTest {
    private JSONObject room() throws Exception {
        return new JSONObject().put("members", new JSONObject().put("AI-01", true).put("AI-02", true).put("AI-03", true));
    }
    @Test public void acceptsOnlyCurrentRoomRecipients() throws Exception {
        JSONObject accepted=FirebaseMessageAdmission.validate("AI-01",new JSONArray().put("AI-02").put("AI-03"),room());
        assertTrue(accepted.optBoolean("AI-02")); assertTrue(accepted.optBoolean("AI-03")); assertEquals(2,accepted.length());
    }
    @Test(expected=IllegalStateException.class) public void rejectsSenderOutsideRoom() throws Exception {
        FirebaseMessageAdmission.validate("AI-04",new JSONArray().put("AI-02"),room());
    }
    @Test(expected=IllegalStateException.class) public void rejectsRecipientOutsideRoom() throws Exception {
        FirebaseMessageAdmission.validate("AI-01",new JSONArray().put("AI-99"),room());
    }
    @Test(expected=IllegalArgumentException.class) public void rejectsSelfRecipient() throws Exception {
        FirebaseMessageAdmission.validate("AI-01",new JSONArray().put("AI-01"),room());
    }
    @Test(expected=IllegalArgumentException.class) public void rejectsDuplicateRecipients() throws Exception {
        FirebaseMessageAdmission.validate("AI-01",new JSONArray().put("AI-02").put("AI-02"),room());
    }
    @Test(expected=IllegalArgumentException.class) public void rejectsEmptyRecipientList() throws Exception {
        FirebaseMessageAdmission.validate("AI-01",new JSONArray(),room());
    }
    @Test(expected=IllegalStateException.class) public void rejectsMissingConversation() throws Exception {
        FirebaseMessageAdmission.validate("AI-01",new JSONArray().put("AI-02"),null);
    }
}