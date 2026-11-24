package com.vidiftmax.aibridgebrowser;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.HashSet;
import java.util.Set;
/** Enforces server-room membership before a Firebase message is written. */
public final class FirebaseMessageAdmission {
    private FirebaseMessageAdmission() { }
    public static JSONObject validate(String senderAiId, JSONArray requestedRecipients,
                                      JSONObject remoteConversation) throws Exception {
        String sender = MessengerRemoteConfig.validateAiId(senderAiId);
        if (remoteConversation == null) throw new IllegalStateException("firebase_conversation_not_found");
        JSONObject members = remoteConversation.optJSONObject("members");
        if (members == null || !members.optBoolean(sender, false))
            throw new IllegalStateException("firebase_sender_not_room_member");
        if (requestedRecipients == null || requestedRecipients.length() < 1)
            throw new IllegalArgumentException("message_recipients_required");
        Set<String> seen = new HashSet<>();
        JSONObject accepted = new JSONObject();
        for (int i = 0; i < requestedRecipients.length(); i++) {
            String recipient = MessengerRemoteConfig.validateAiId(requestedRecipients.optString(i, ""));
            if (sender.equals(recipient) || !seen.add(recipient))
                throw new IllegalArgumentException("invalid_message_recipient");
            if (!members.optBoolean(recipient, false))
                throw new IllegalStateException("firebase_recipient_not_room_member");
            accepted.put(recipient, true);
        }
        if (members.length() > 20 || accepted.length() > 19)
            throw new IllegalStateException("firebase_room_member_limit_exceeded");
        return accepted;
    }
}