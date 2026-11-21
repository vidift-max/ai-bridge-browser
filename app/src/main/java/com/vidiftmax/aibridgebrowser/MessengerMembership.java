package com.vidiftmax.aibridgebrowser;

/** Local-only membership proposal; it does not invite or join a remote participant. */
public final class MessengerMembership {
    public enum State { LOCAL_SELECTED, INVITE_PENDING, JOINED_VERIFIED, REMOVED }

    private final String conversationId;
    private final String participantLocalId;
    private final State state;

    public MessengerMembership(String conversationId, String participantLocalId) {
        if (conversationId == null || conversationId.trim().isEmpty())
            throw new IllegalArgumentException("conversationId obrigatório");
        if (participantLocalId == null || !participantLocalId.matches("CONTACT-[A-Za-z0-9-]{8,80}"))
            throw new IllegalArgumentException("participante local inválido");
        this.conversationId = conversationId;
        this.participantLocalId = participantLocalId;
        this.state = State.LOCAL_SELECTED;
    }

    public String getConversationId() { return conversationId; }
    public String getParticipantLocalId() { return participantLocalId; }
    public State getState() { return state; }
}
