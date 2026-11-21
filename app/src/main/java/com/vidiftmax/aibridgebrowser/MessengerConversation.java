package com.vidiftmax.aibridgebrowser;

import java.util.UUID;

/** A conversation created on this device; it does not imply a remote participant or room. */
public final class MessengerConversation {
    public static final String KIND_LOCAL_SANDBOX = "LOCAL_SANDBOX";
    public static final String STATUS_LOCAL_ONLY = "LOCAL_ONLY";
    private final String conversationId;
    private final String title;
    private final long createdAtEpochMs;

    public MessengerConversation(String title, long createdAtEpochMs) {
        if (title == null || title.trim().isEmpty())
            throw new IllegalArgumentException("título obrigatório");
        if (title.trim().length() > 60)
            throw new IllegalArgumentException("título excede 60 caracteres");
        if (createdAtEpochMs <= 0)
            throw new IllegalArgumentException("timestamp inválido");
        this.conversationId = "LOCAL-" + UUID.randomUUID();
        this.title = title.trim();
        this.createdAtEpochMs = createdAtEpochMs;
    }
    public String getConversationId() { return conversationId; }
    public String getTitle() { return title; }
    public long getCreatedAtEpochMs() { return createdAtEpochMs; }
    public String getKind() { return KIND_LOCAL_SANDBOX; }
    public String getStatus() { return STATUS_LOCAL_ONLY; }
}
