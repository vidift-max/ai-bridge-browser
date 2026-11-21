package com.vidiftmax.aibridgebrowser;

import java.util.UUID;

/** Local contact card only. It is not an authenticated AI identity or a live presence record. */
public final class MessengerParticipant {
    public enum State {
        LOCAL_DRAFT,
        INVITED_LOCAL,
        ACCEPTED_LOCAL,
        PENDING_VERIFICATION,
        ACTIVE,
        DISCONNECTED,
        SUSPENDED,
        REVOKED
    }

    private final String localId;
    private final String displayName;
    private final String provider;
    private final State state;
    private final String aiId;
    private final String phoneNumber;
    private final String serial;

    public MessengerParticipant(String displayName, String provider) {
        if (displayName == null || displayName.trim().isEmpty())
            throw new IllegalArgumentException("Nome da IA é obrigatório");
        if (displayName.trim().length() > 80)
            throw new IllegalArgumentException("Nome excede 80 caracteres");
        if (provider == null || provider.trim().isEmpty())
            throw new IllegalArgumentException("Provedor é obrigatório");
        if (provider.trim().length() > 80)
            throw new IllegalArgumentException("Provedor excede 80 caracteres");
        this.localId = "CONTACT-" + UUID.randomUUID();
        this.displayName = displayName.trim();
        this.provider = provider.trim();
        this.state = State.LOCAL_DRAFT;
        this.aiId = null;
        this.phoneNumber = null;
        this.serial = null;
    }

    private MessengerParticipant(String localId, String displayName, String provider, State state,
                                 String aiId, String phoneNumber, String serial) {
        this.localId = localId;
        this.displayName = displayName;
        this.provider = provider;
        this.state = state;
        this.aiId = aiId;
        this.phoneNumber = phoneNumber;
        this.serial = serial;
    }

    public static MessengerParticipant fromLocalRecord(String localId, String displayName,
            String provider, String state, String aiId, String phoneNumber, String serial) {
        if (localId == null || !localId.matches("CONTACT-[A-Za-z0-9-]{8,80}"))
            throw new IllegalArgumentException("Identificador local inválido");
        if (displayName == null || displayName.trim().isEmpty() ||
                provider == null || provider.trim().isEmpty())
            throw new IllegalArgumentException("Nome e provedor são obrigatórios");
        final State parsed;
        try { parsed = State.valueOf(state); }
        catch (RuntimeException invalid) { throw new IllegalArgumentException("Estado inválido"); }

        boolean anyRegistryField = aiId != null || phoneNumber != null || serial != null;
        if (anyRegistryField) {
            if (aiId == null || !aiId.matches("AI-[A-Z0-9][A-Z0-9-]{1,62}") ||
                    phoneNumber == null || !phoneNumber.matches("AI-PHONE-[0-9]{3,}") ||
                    serial == null || !serial.matches("AIP-[0-9]{4}-[0-9]{6,}"))
                throw new IllegalArgumentException("Dados de identidade oficial incompletos ou inválidos");
        }
        if ((parsed == State.ACTIVE || parsed == State.DISCONNECTED ||
                parsed == State.SUSPENDED || parsed == State.REVOKED) && !anyRegistryField)
            throw new IllegalArgumentException("Estado de conta exige identidade oficial completa");
        return new MessengerParticipant(localId, displayName.trim(), provider.trim(),
                parsed, aiId, phoneNumber, serial);
    }

    public String getLocalId() { return localId; }
    public String getDisplayName() { return displayName; }
    public String getProvider() { return provider; }
    public State getState() { return state; }
    public String getAiId() { return aiId; }
    public String getPhoneNumber() { return phoneNumber; }
    public String getSerial() { return serial; }
    public boolean hasVerifiedRegistryIdentity() {
        return aiId != null && phoneNumber != null && serial != null;
    }
}
