package com.vidiftmax.aibridgebrowser;

import org.json.JSONObject;
import org.junit.Test;

import java.util.List;

import static org.junit.Assert.*;

public class VoiceIceCandidateBufferTest {
    @Test public void buffersCandidatesInArrivalOrderUntilDrain() throws Exception {
        VoiceIceCandidateBuffer buffer = new VoiceIceCandidateBuffer();
        VoiceSignalPayload.IceCandidateData first = VoiceSignalPayload.readIceCandidate(
                new JSONObject().put("candidate", "candidate:first").put("sdpMLineIndex", 0));
        VoiceSignalPayload.IceCandidateData second = VoiceSignalPayload.readIceCandidate(
                new JSONObject().put("candidate", "candidate:second").put("sdpMLineIndex", 1));
        buffer.add(first);
        buffer.add(second);
        assertEquals(2, buffer.size());
        List<VoiceSignalPayload.IceCandidateData> drained = buffer.drain();
        assertEquals(2, drained.size());
        assertEquals("candidate:first", drained.get(0).candidate);
        assertEquals("candidate:second", drained.get(1).candidate);
        assertEquals(0, buffer.size());
    }

    @Test public void clearDiscardsCandidatesFromEndedCall() throws Exception {
        VoiceIceCandidateBuffer buffer = new VoiceIceCandidateBuffer();
        buffer.add(VoiceSignalPayload.readIceCandidate(
                new JSONObject().put("candidate", "candidate:discard").put("sdpMLineIndex", 0)));
        buffer.clear();
        assertTrue(buffer.drain().isEmpty());
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsNullCandidate() {
        new VoiceIceCandidateBuffer().add(null);
    }
}
