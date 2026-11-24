package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Pure validation rules for linking the collective room to an authenticated group. */
public final class CollectiveRoomRemotePolicy {
    private CollectiveRoomRemotePolicy() { }

    public static List<String> recipients(List<String> members, String ownAiId) {
        String own = MessengerRemoteConfig.validateAiId(ownAiId);
        if (members == null || members.size() < 2 || members.size() > 20) {
            throw new IllegalArgumentException("remote_room_member_count_invalid");
        }
        Set<String> seen = new HashSet<>();
        List<String> recipients = new ArrayList<>();
        boolean includesSelf = false;
        for (String raw : members) {
            String member = MessengerRemoteConfig.validateAiId(raw);
            if (!seen.add(member)) throw new IllegalArgumentException("remote_room_duplicate_member");
            if (own.equals(member)) includesSelf = true;
            else recipients.add(member);
        }
        if (!includesSelf) throw new IllegalArgumentException("remote_room_own_identity_missing");
        if (recipients.isEmpty()) throw new IllegalArgumentException("remote_room_recipients_missing");
        return recipients;
    }

    public static boolean hasSeen(Set<String> seenMessageIds, String messageId) {
        if (seenMessageIds == null || messageId == null || messageId.trim().isEmpty()) {
            throw new IllegalArgumentException("remote_message_id_required");
        }
        return seenMessageIds.contains(messageId.trim());
    }
}
