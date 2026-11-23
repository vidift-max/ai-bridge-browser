package com.vidiftmax.aibridgebrowser;

import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class VoiceRoomControlTest {
    @Test public void adminCanMuteAndReleaseParticipant() {
        VoiceRoomControl control = new VoiceRoomControl("AI-GPT6");
        control.mute("AI-GPT6", "AI-02");
        assertTrue(control.isMuted("AI-02"));
        control.unmute("AI-GPT6", "AI-02");
        assertFalse(control.isMuted("AI-02"));
    }

    @Test(expected = SecurityException.class)
    public void nonAdminCannotMuteParticipant() {
        VoiceRoomControl control = new VoiceRoomControl("AI-GPT6");
        control.mute("AI-02", "AI-03");
    }

    @Test(expected = IllegalArgumentException.class)
    public void adminCannotMuteSelf() {
        VoiceRoomControl control = new VoiceRoomControl("AI-GPT6");
        control.mute("AI-GPT6", "AI-GPT6");
    }
}
