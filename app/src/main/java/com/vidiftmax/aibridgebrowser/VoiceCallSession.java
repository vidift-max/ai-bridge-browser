package com.vidiftmax.aibridgebrowser;

/** Pure local call-state guard. It does not create a peer connection or transmit audio. */
public final class VoiceCallSession {
    public enum State {
        IDLE, OUTGOING_RINGING, INCOMING_RINGING, ACCEPTED, CONNECTING,
        CONNECTED, REJECTED, CANCELLED, BUSY, TIMED_OUT, ENDED, FAILED
    }

    private State state = State.IDLE;
    private String callId = "";

    public synchronized State state() { return state; }
    public synchronized String callId() { return callId; }

    public synchronized void outgoing(String id) {
        requireId(id);
        if (state != State.IDLE && terminal(state)) throw new IllegalStateException("call_reset_required");
        if (state != State.IDLE) throw new IllegalStateException("call_already_active");
        callId = id;
        state = State.OUTGOING_RINGING;
    }

    public synchronized void incoming(String id) {
        requireId(id);
        if (state != State.IDLE) throw new IllegalStateException("call_already_active");
        callId = id;
        state = State.INCOMING_RINGING;
    }

    public synchronized void applyServerState(String id, String serverState) {
        requireCurrent(id);
        State next;
        try { next = State.valueOf(serverState); }
        catch (Exception invalid) { throw new IllegalArgumentException("invalid_server_call_state"); }
        if (state == next) return;
        if (terminal(state)) throw new IllegalStateException("call_is_terminal");
        if (!allowed(state, next)) throw new IllegalStateException("invalid_local_call_transition");
        state = next;
    }

    public synchronized void reset() {
        if (state != State.IDLE && !terminal(state)) throw new IllegalStateException("active_call_cannot_reset");
        state = State.IDLE;
        callId = "";
    }

    private void requireCurrent(String id) {
        requireId(id);
        if (!callId.equals(id)) throw new IllegalArgumentException("voice_call_id_mismatch");
    }

    private static void requireId(String id) {
        if (id == null || !id.matches("[A-Za-z0-9-]{1,80}"))
            throw new IllegalArgumentException("invalid_voice_call_id");
    }

    private static boolean terminal(State value) {
        return value == State.REJECTED || value == State.CANCELLED || value == State.BUSY
                || value == State.TIMED_OUT || value == State.ENDED || value == State.FAILED;
    }

    private static boolean allowed(State from, State to) {
        switch (from) {
            case OUTGOING_RINGING:
                return to == State.ACCEPTED || to == State.REJECTED || to == State.CANCELLED
                        || to == State.BUSY || to == State.TIMED_OUT || to == State.FAILED;
            case INCOMING_RINGING:
                return to == State.ACCEPTED || to == State.REJECTED || to == State.CANCELLED
                        || to == State.BUSY || to == State.TIMED_OUT || to == State.FAILED;
            case ACCEPTED:
                return to == State.CONNECTING || to == State.ENDED || to == State.FAILED;
            case CONNECTING:
                return to == State.CONNECTED || to == State.ENDED || to == State.FAILED;
            case CONNECTED:
                return to == State.ENDED || to == State.FAILED;
            default:
                return false;
        }
    }
}
