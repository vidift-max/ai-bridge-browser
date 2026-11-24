package com.vidiftmax.aibridgebrowser;

import org.junit.Test;

import static org.junit.Assert.*;

public class VoiceIceServerConfigTest {
    @Test public void emptyConfigMeansNoImplicitServers() throws Exception {
        assertTrue(VoiceIceServerConfig.parse("").isEmpty());
        assertTrue(VoiceIceServerConfig.parse("[]").isEmpty());
    }

    @Test public void acceptsStunUrlWithoutCredentials() throws Exception {
        assertEquals(1, VoiceIceServerConfig.parse(
                "[{\"url\":\"stun:stun.example.invalid:3478\"}]").size());
    }

    @Test public void acceptsTurnUrlOnlyWithCredentials() throws Exception {
        assertEquals(1, VoiceIceServerConfig.parse(
                "[{\"url\":\"turn:turn.example.invalid:3478?transport=udp\",\"username\":\"u\",\"password\":\"p\"}]").size());
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsTurnWithoutCredentials() throws Exception {
        VoiceIceServerConfig.parse("[{\"url\":\"turn:turn.example.invalid:3478\"}]");
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsCredentialsOnStun() throws Exception {
        VoiceIceServerConfig.parse(
                "[{\"url\":\"stun:stun.example.invalid:3478\",\"username\":\"u\",\"password\":\"p\"}]");
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsUnsupportedScheme() throws Exception {
        VoiceIceServerConfig.parse("[{\"url\":\"https://example.invalid\"}]");
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsTooManyServers() throws Exception {
        VoiceIceServerConfig.parse("[{\"url\":\"stun:a\"},{\"url\":\"stun:b\"},{\"url\":\"stun:c\"},{\"url\":\"stun:d\"},{\"url\":\"stun:e\"}]");
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsWhitespaceInUrl() throws Exception {
        VoiceIceServerConfig.parse("[{\"url\":\"turn:bad host\"}]");
    }
}
