package com.vidiftmax.aibridgebrowser;

import java.util.UUID;

/**
 * Local idempotency key for a Messenger operation.
 * This is only a local duplicate-prevention primitive; it is not a server ACK.
 */
public final class MessengerLocalOperation {
    private final String operationId;
    private final String messageId;
    private final String operation;
    private final long createdAtEpochMs;

    public MessengerLocalOperation(String messageId, String operation, long createdAtEpochMs) {
        if (messageId == null || messageId.trim().isEmpty())
            throw new IllegalArgumentException("messageId obrigatório");
        if (operation == null || operation.trim().isEmpty())
            throw new IllegalArgumentException("operation obrigatória");
        if (createdAtEpochMs <= 0)
            throw new IllegalArgumentException("timestamp inválido");
        this.operationId = "LOCAL-OP-" + UUID.randomUUID();
        this.messageId = messageId.trim();
        this.operation = operation.trim();
        this.createdAtEpochMs = createdAtEpochMs;
    }

    public String getOperationId() { return operationId; }
    public String getMessageId() { return messageId; }
    public String getOperation() { return operation; }
    public long getCreatedAtEpochMs() { return createdAtEpochMs; }
}
