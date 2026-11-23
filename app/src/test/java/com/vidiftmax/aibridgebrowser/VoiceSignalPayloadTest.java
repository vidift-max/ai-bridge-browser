package com.vidiftmax.aibridgebrowser;

import org.json.JSONObject;
import org.junit.Test;

import static org.junit.Assert.*;

public class VoiceSignalPayloadTest {
    @Test public void offerPayloadMatchesServerContract() throws Exception {
        JSONObject payload = VoiceSignalPayload.sessionDescription("offer", "v=0\r\n");
        assertEquals("offer", payload.getString("type"));
        assertEquals("v=0\r\n", payload.getString("sdp"));
    }

    @Test public void answerPayloadMatchesServerContract() throws Exception {
        assertEquals("answer", VoiceSignalPayload.sessionDescription("answer", "v=0").getString("type"));
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsUnexpectedSdpType() throws Exception {
        VoiceSignalPayload.sessionDescription("pranswer", "v=0");
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsOversizedSdp() throws Exception {
        VoiceSignalPayload.sessionDescription("offer", new String(new char[18001]).replace('\0', 'x'));
    }

    @Test public void iceCandidateRoundTripsOptionalFields() throws Exception {
        JSONObject json = VoiceSignalPayload.iceCandidate(
                "candidate:1 1 UDP 1 192.0.2.1 10000 typ host", "audio", 0, "ufrag");
        VoiceSignalPayload.IceCandidateData parsed = VoiceSignalPayload.readIceCandidate(json);
        assertEquals("candidate:1 1 UDP 1 192.0.2.1 10000 typ host", parsed.candidate);
        assertEquals("audio", parsed.sdpMid);
        assertEquals(0, parsed.sdpMLineIndex);
        assertEquals("ufrag", parsed.usernameFragment);
    }

    @Test public void iceCompleteIsEmptyObject() throws Exception {
        assertEquals(0, VoiceSignalPayload.iceComplete().length());
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsInvalidIceLineIndex() throws Exception {
        VoiceSignalPayload.iceCandidate("candidate:1", "audio", -1, null);
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsEmptyCandidate() throws Exception {
        VoiceSignalPayload.iceCandidate(" ", "audio", 0, null);
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsMalformedRemoteCandidate() {
        VoiceSignalPayload.readIceCandidate(new JSONObject().put("candidate", "candidate:1"));
    }
}
