package com.vidiftmax.aibridgebrowser;

public final class MessengerSession {
    private final String sessionId;
    private final String aiId;
    private final String providerSubject;

    public MessengerSession(String sessionId, String aiId, String providerSubject) {
        this.sessionId = require(sessionId, "sessionId");
        this.aiId = require(aiId, "aiId");
        this.providerSubject = require(providerSubject, "providerSubject");
    }

    public String getSessionId() { return sessionId; }
    public String getAiId() { return aiId; }
    public String getProviderSubject() { return providerSubject; }

    private static String require(String value, String field) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException(field + " is required");
        }
        return value;
    }
}
