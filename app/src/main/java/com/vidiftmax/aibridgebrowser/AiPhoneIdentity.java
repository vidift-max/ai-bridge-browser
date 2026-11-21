package com.vidiftmax.aibridgebrowser;

/**
 * Read-only client representation of an AI participant identity.
 *
 * This class validates registry-shaped data; it does not authenticate a server,
 * allocate identifiers, or prove that a supplied record is genuine.
 */
public final class AiPhoneIdentity {
    public enum Status { INVITED, ACCEPTED_PENDING_VERIFICATION, ACTIVE, SUSPENDED, REVOKED }

    private final String aiId;
    private final String displayName;
    private final String provider;
    private final Status status;
    private final String displayNumber;
    private final String serial;

    private AiPhoneIdentity(String aiId, String displayName, String provider,
                            Status status, String displayNumber, String serial) {
        this.aiId = aiId;
        this.displayName = displayName;
        this.provider = provider;
        this.status = status;
        this.displayNumber = displayNumber;
        this.serial = serial;
    }

    public static AiPhoneIdentity unassigned() {
        return new AiPhoneIdentity(null, "Participante não associado", null,
                Status.INVITED, null, null);
    }

    /**
     * Parses a record expected to have come from an authenticated registry API.
     * Callers must independently authenticate the transport and authorize access.
     */
    public static AiPhoneIdentity fromRegistryRecord(
            String aiId, String displayName, String provider, String status,
            String displayNumber, String serial) {
        if (!matches(aiId, "AI-[A-Z0-9][A-Z0-9-]{1,62}")) {
            throw new IllegalArgumentException("AI_ID ausente ou inválido");
        }
        if (blank(displayName) || blank(provider)) {
            throw new IllegalArgumentException("Nome e provedor são obrigatórios");
        }
        final Status parsedStatus;
        try {
            parsedStatus = Status.valueOf(status);
        } catch (RuntimeException invalidStatus) {
            throw new IllegalArgumentException("Estado de identidade inválido");
        }
        if (!matches(displayNumber, "AI-PHONE-[0-9]{3,}") ||
                !matches(serial, "AIP-[0-9]{4}-[0-9]{6,}")) {
            throw new IllegalArgumentException("Número ou série do registro inválido");
        }
        return new AiPhoneIdentity(aiId, displayName.trim(), provider.trim(),
                parsedStatus, displayNumber, serial);
    }

    public boolean isRegistryAssigned() {
        return aiId != null && displayNumber != null && serial != null;
    }
    public String getAiId() { return aiId; }
    public String getDisplayName() { return displayName; }
    public String getProvider() { return provider; }
    public Status getStatus() { return status; }
    public String getDisplayNumber() { return displayNumber; }
    public String getSerial() { return serial; }

    private static boolean blank(String value) {
        return value == null || value.trim().isEmpty();
    }
    private static boolean matches(String value, String regex) {
        return value != null && value.matches(regex);
    }
}
