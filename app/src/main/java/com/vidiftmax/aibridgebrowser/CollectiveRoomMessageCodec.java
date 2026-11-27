package com.vidiftmax.aibridgebrowser;

/** Encodes and parses one locally persisted collective-room message line. */
public final class CollectiveRoomMessageCodec {
    private CollectiveRoomMessageCodec() { }

    public static String encode(long createdAtEpochMs, String kind,
                                String sender, String avatar, String body) {
        if (createdAtEpochMs <= 0) throw new IllegalArgumentException("invalid_message_timestamp");
        return createdAtEpochMs + "|"
                + MessengerRetentionPolicy.normalizeMessageKind(kind) + "|"
                + safe(sender) + "|" + safe(avatar) + "|" + safe(body);
    }

    public static Message decode(String line) {
        if (line == null) return null;
        String[] fields = line.split("\\|", 5);
        if (fields.length != 5) return null;
        try {
            long created = Long.parseLong(fields[0]);
            if (created <= 0) return null;
            return new Message(created,
                    MessengerRetentionPolicy.normalizeMessageKind(fields[1]),
                    fields[2], fields[3], fields[4]);
        } catch (NumberFormatException invalid) {
            return null;
        }
    }

    private static String safe(String value) {
        if (value == null) return "";
        return value.replace("|", "¦").replace("\r", " ").replace("\n", " ");
    }

    public static final class Message {
        public final long createdAtEpochMs;
        public final String kind;
        public final String sender;
        public final String avatar;
        public final String body;

        private Message(long createdAtEpochMs, String kind, String sender,
                        String avatar, String body) {
            this.createdAtEpochMs = createdAtEpochMs;
            this.kind = kind;
            this.sender = sender;
            this.avatar = avatar;
            this.body = body;
        }
    }
}
