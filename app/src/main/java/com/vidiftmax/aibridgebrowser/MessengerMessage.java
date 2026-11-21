package com.vidiftmax.aibridgebrowser;

import java.util.UUID;

/** A locally stored messenger item; never represents remote delivery. */
public final class MessengerMessage {
    public static final String STATUS_LOCAL_ONLY = "LOCAL_ONLY";
    private final String messageId;
    private final String conversationId;
    private final String senderLabel;
    private final String body;
    private final long createdAtEpochMs;
    private final String status;

    public MessengerMessage(String conversationId, String senderLabel, String body, long createdAtEpochMs) {
        if (conversationId == null || conversationId.trim().isEmpty())
            throw new IllegalArgumentException("conversationId obrigatório");
        if (senderLabel == null || senderLabel.trim().isEmpty())
            throw new IllegalArgumentException("senderLabel obrigatório");
        if (body == null || body.trim().isEmpty())
            throw new IllegalArgumentException("body obrigatório");
        if (body.length() > 4000)
            throw new IllegalArgumentException("mensagem excede 4000 caracteres");
        if (createdAtEpochMs <= 0)
            throw new IllegalArgumentException("timestamp inválido");
        this.messageId = UUID.randomUUID().toString();
        this.conversationId = conversationId;
        this.senderLabel = senderLabel.trim();
        this.body = body.trim();
        this.createdAtEpochMs = createdAtEpochMs;
        this.status = STATUS_LOCAL_ONLY;
    }
    public String getMessageId() { return messageId; }
    public String getConversationId() { return conversationId; }
    public String getSenderLabel() { return senderLabel; }
    public String getBody() { return body; }
    public long getCreatedAtEpochMs() { return createdAtEpochMs; }
    public String getStatus() { return status; }
}
