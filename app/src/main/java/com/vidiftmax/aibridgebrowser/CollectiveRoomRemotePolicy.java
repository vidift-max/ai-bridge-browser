package com.vidiftmax.aibridgebrowser;

import org.json.JSONArray;
import org.json.JSONException;

import java.util.HashSet;
import java.util.Set;

/** Pure validation rules for linking the collective room to an authenticated group. */
public final class CollectiveRoomRemotePolicy {
    private CollectiveRoomRemotePolicy() { }

    public static JSONArray recipients(JSONArray members, String ownAiId) throws JSONException {
        String own = MessengerRemoteConfig.validateAiId(ownAiId);
        if (members == null || members.length() < 2 || members.length() > 20) {
            throw new IllegalArgumentException("remote_room_member_count_invalid");
        }
        Set<String> seen = new HashSet<>();
        JSONArray recipients = new JSONArray();
        boolean includesSelf = false;
        for (int i = 0; i < members.length(); i++) {
            String member = MessengerRemoteConfig.validateAiId(members.optString(i, ""));
            if (!seen.add(member)) throw new IllegalArgumentException("remote_room_duplicate_member");
            if (own.equals(member)) includesSelf = true;
            else recipients.put(member);
        }
        if (!includesSelf) throw new IllegalArgumentException("remote_room_own_identity_missing");
        if (recipients.length() == 0) throw new IllegalArgumentException("remote_room_recipients_missing");
        return recipients;
    }

    public static boolean hasSeen(Set<String> seenMessageIds, String messageId) {
        if (seenMessageIds == null || messageId == null || messageId.trim().isEmpty()) {
            throw new IllegalArgumentException("remote_message_id_required");
        }
        return seenMessageIds.contains(messageId.trim());
    }
}
