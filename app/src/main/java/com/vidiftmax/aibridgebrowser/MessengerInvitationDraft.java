package com.vidiftmax.aibridgebrowser;

/** A local invitation draft; it is never transmitted by this class. */
public final class MessengerInvitationDraft {
    public static final String STATUS_LOCAL_DRAFT = "LOCAL_DRAFT";
    private final String invitationId;
    private final String participantLocalId;
    private final String body;

    public MessengerInvitationDraft(String participantLocalId, String body) {
        if (participantLocalId == null || !participantLocalId.matches("CONTACT-[A-Za-z0-9-]{8,80}"))
            throw new IllegalArgumentException("participante local inválido");
        if (body == null || body.trim().isEmpty())
            throw new IllegalArgumentException("texto do convite obrigatório");
        if (body.trim().length() > 5000)
            throw new IllegalArgumentException("texto do convite excede 5000 caracteres");
        this.invitationId = "INVITE-LOCAL-" + java.util.UUID.randomUUID();
        this.participantLocalId = participantLocalId;
        this.body = body.trim();
    }

    public String getInvitationId() { return invitationId; }
    public String getParticipantLocalId() { return participantLocalId; }
    public String getBody() { return body; }
    public String getStatus() { return STATUS_LOCAL_DRAFT; }
}
