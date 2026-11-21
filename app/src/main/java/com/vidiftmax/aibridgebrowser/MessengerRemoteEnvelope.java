package com.vidiftmax.aibridgebrowser;

/** Minimal contract-shaped envelope for a future authenticated transport. */
public final class MessengerRemoteEnvelope {
    private final String messageId;
    private final String conversationId;
    private final String payloadType;
    private final String body;

    public MessengerRemoteEnvelope(String messageId, String conversationId, String payloadType, String body) {
        this.messageId = require(messageId, "messageId");
        this.conversationId = require(conversationId, "conversationId");
        this.payloadType = require(payloadType, "payloadType");
        this.body = require(body, "body");
    }

    public String getMessageId() { return messageId; }
    public String getConversationId() { return conversationId; }
    public String getPayloadType() { return payloadType; }
    public String getBody() { return body; }

    private static String require(String value, String field) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException(field + " is required");
        }
        return value;
    }
}
