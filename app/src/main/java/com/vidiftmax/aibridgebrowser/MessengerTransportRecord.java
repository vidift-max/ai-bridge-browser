package com.vidiftmax.aibridgebrowser;

import java.util.UUID;

/**
 * Local-only inbox/outbox record.
 * It never proves remote transport, delivery, authentication or provider connectivity.
 */
public final class MessengerTransportRecord {
    public static final String DIRECTION_OUTBOX = "LOCAL_OUTBOX";
    public static final String DIRECTION_INBOX = "LOCAL_INBOX";
    public static final String STATUS_LOCAL_ONLY = "LOCAL_ONLY";

    private final String recordId;
    private final String messageId;
    private final String conversationId;
    private final String direction;
    private final String participantLocalId;
    private final long createdAtEpochMs;
    private final String status;

    public MessengerTransportRecord(
            String messageId,
            String conversationId,
            String direction,
            String participantLocalId,
            long createdAtEpochMs) {
        if (messageId == null || messageId.trim().isEmpty())
            throw new IllegalArgumentException("messageId obrigatório");
        if (conversationId == null || conversationId.trim().isEmpty())
            throw new IllegalArgumentException("conversationId obrigatório");
        if (!DIRECTION_OUTBOX.equals(direction) && !DIRECTION_INBOX.equals(direction))
            throw new IllegalArgumentException("direção local inválida");
        if (participantLocalId == null || participantLocalId.trim().isEmpty())
            throw new IllegalArgumentException("participantLocalId obrigatório");
        if (createdAtEpochMs <= 0)
            throw new IllegalArgumentException("timestamp inválido");
        this.recordId = "LOCAL-TRANSPORT-" + UUID.randomUUID();
        this.messageId = messageId.trim();
        this.conversationId = conversationId.trim();
        this.direction = direction;
        this.participantLocalId = participantLocalId.trim();
        this.createdAtEpochMs = createdAtEpochMs;
        this.status = STATUS_LOCAL_ONLY;
    }

    public String getRecordId() { return recordId; }
    public String getMessageId() { return messageId; }
    public String getConversationId() { return conversationId; }
    public String getDirection() { return direction; }
    public String getParticipantLocalId() { return participantLocalId; }
    public long getCreatedAtEpochMs() { return createdAtEpochMs; }
    public String getStatus() { return status; }
}
