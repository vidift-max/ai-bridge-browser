package com.vidiftmax.aibridgebrowser;

import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.Set;

/**
 * Local room policy model for future real-time voice calls.
 *
 * This class does not access the microphone and does not mute Android audio.
 * It only tracks which AI participants are temporarily muted by the room admin.
 */
public final class VoiceRoomControl {
    private final String adminAiId;
    private final Set<String> mutedAiIds = new LinkedHashSet<>();

    public VoiceRoomControl(String adminAiId) {
        if (adminAiId == null || adminAiId.trim().isEmpty()) {
            throw new IllegalArgumentException("admin_ai_id_required");
        }
        this.adminAiId = adminAiId.trim();
    }

    public String adminAiId() {
        return adminAiId;
    }

    public void mute(String actingAiId, String targetAiId) {
        authorizeAdmin(actingAiId);
        validateTarget(targetAiId);
        if (adminAiId.equals(targetAiId.trim())) {
            throw new IllegalArgumentException("admin_cannot_mute_self");
        }
        mutedAiIds.add(targetAiId.trim());
    }

    public void unmute(String actingAiId, String targetAiId) {
        authorizeAdmin(actingAiId);
        validateTarget(targetAiId);
        mutedAiIds.remove(targetAiId.trim());
    }

    public boolean isMuted(String aiId) {
        return aiId != null && mutedAiIds.contains(aiId.trim());
    }

    public Set<String> mutedAiIds() {
        return Collections.unmodifiableSet(new LinkedHashSet<>(mutedAiIds));
    }

    private void authorizeAdmin(String actingAiId) {
        if (actingAiId == null || !adminAiId.equals(actingAiId.trim())) {
            throw new SecurityException("voice_admin_required");
        }
    }

    private static void validateTarget(String targetAiId) {
        if (targetAiId == null || targetAiId.trim().isEmpty()) {
            throw new IllegalArgumentException("target_ai_id_required");
        }
    }
}
