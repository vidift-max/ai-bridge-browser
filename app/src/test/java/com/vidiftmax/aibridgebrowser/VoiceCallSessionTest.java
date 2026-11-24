package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import static org.junit.Assert.*;

public class VoiceCallSessionTest {
    @Test public void outgoingCallCanConnectAndEnd() {
        VoiceCallSession session = new VoiceCallSession();
        session.outgoing("call-001");
        assertEquals(VoiceCallSession.State.OUTGOING_RINGING, session.state());
        session.applyServerState("call-001", "ACCEPTED");
        session.applyServerState("call-001", "CONNECTING");
        session.applyServerState("call-001", "CONNECTED");
        session.applyServerState("call-001", "ENDED");
        assertEquals(VoiceCallSession.State.ENDED, session.state());
    }

    @Test public void incomingCallCanBeRejected() {
        VoiceCallSession session = new VoiceCallSession();
        session.incoming("call-002");
        session.applyServerState("call-002", "REJECTED");
        assertEquals(VoiceCallSession.State.REJECTED, session.state());
    }

    @Test(expected = IllegalStateException.class)
    public void cannotConnectBeforeAccept() {
        VoiceCallSession session = new VoiceCallSession();
        session.outgoing("call-001");
        session.applyServerState("call-001", "CONNECTED");
    }

    @Test(expected = IllegalStateException.class)
    public void terminalCallCannotBeReopened() {
        VoiceCallSession session = new VoiceCallSession();
        session.incoming("call-002");
        session.applyServerState("call-002", "TIMED_OUT");
        session.applyServerState("call-002", "ACCEPTED");
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsStateForAnotherCall() {
        VoiceCallSession session = new VoiceCallSession();
        session.outgoing("call-001");
        session.applyServerState("call-002", "ACCEPTED");
    }

    @Test public void terminalCallMustBeResetBeforeNextCall() {
        VoiceCallSession session = new VoiceCallSession();
        session.outgoing("call-001");
        session.applyServerState("call-001", "CANCELLED");
        session.reset();
        session.incoming("call-002");
        assertEquals("call-002", session.callId());
    }
}
