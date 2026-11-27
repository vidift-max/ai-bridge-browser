package com.vidiftmax.aibridgebrowser;

/**
 * Retention rules shared by the local Messenger UI and its tests.
 * NORMAL group messages live for one hour; mission messages and private
 * conversation messages live for 24 hours. Audio attached to a message
 * follows the message retention window.
 */
public final class MessengerRetentionPolicy {
    public static final String MESSAGE_NORMAL = "NORMAL";
    public static final String MESSAGE_MISSION = "MISSION";
    public static final String CONVERSATION_GROUP = "GROUP";
    public static final String CONVERSATION_PRIVATE = "PRIVATE";
    public static final long ONE_HOUR_MS = 60L * 60L * 1000L;
    public static final long ONE_DAY_MS = 24L * ONE_HOUR_MS;

    private MessengerRetentionPolicy() {}

    public static long retentionMs(String messageKind, String conversationKind) {
        if (MESSAGE_MISSION.equals(normalizeMessageKind(messageKind))
                || CONVERSATION_PRIVATE.equals(normalizeConversationKind(conversationKind))) {
            return ONE_DAY_MS;
        }
        return ONE_HOUR_MS;
    }

    public static long expiresAt(long createdAtEpochMs, String messageKind, String conversationKind) {
        if (createdAtEpochMs <= 0) throw new IllegalArgumentException("timestamp inválido");
        return createdAtEpochMs + retentionMs(messageKind, conversationKind);
    }

    public static boolean isExpired(long createdAtEpochMs, String messageKind,
                                    String conversationKind, long nowEpochMs) {
        if (createdAtEpochMs <= 0 || nowEpochMs < 0) return true;
        return nowEpochMs >= expiresAt(createdAtEpochMs, messageKind, conversationKind);
    }

    public static String normalizeMessageKind(String kind) {
        return MESSAGE_MISSION.equals(kind) ? MESSAGE_MISSION : MESSAGE_NORMAL;
    }

    public static String normalizeConversationKind(String kind) {
        return CONVERSATION_PRIVATE.equals(kind) ? CONVERSATION_PRIVATE : CONVERSATION_GROUP;
    }
}
