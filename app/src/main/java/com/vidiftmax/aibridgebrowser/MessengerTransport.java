package com.vidiftmax.aibridgebrowser;

/**
 * Boundary for authenticated remote Messenger transport.
 * Implementations may use HTTP, WebSocket or another authorized mechanism.
 * This interface does not itself claim that any remote operation occurred.
 */
public interface MessengerTransport {
    TransportResult submit(MessengerRemoteEnvelope envelope, String idempotencyKey);

    TransportResult fetchPending(String conversationId, String cursor);

    TransportResult acknowledge(String messageId);

    TransportSessionState sessionState();

    void closeSession();

    enum TransportSessionState {
        LOCAL_ONLY,
        OFFLINE,
        AUTHENTICATION_REQUIRED,
        AUTHENTICATED,
        AUTHORIZATION_DENIED,
        CLOSED
    }

    enum TransportResult {
        ACCEPTED_BY_SERVER,
        PENDING_RETRIEVAL,
        ACKNOWLEDGED_BY_SERVER,
        UNAVAILABLE,
        AUTHENTICATION_REQUIRED,
        AUTHORIZATION_DENIED,
        TEMPORARY_FAILURE,
        IDEMPOTENCY_CONFLICT,
        PERMANENT_REJECTION
    }
}
