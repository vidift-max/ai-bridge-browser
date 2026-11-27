package com.vidiftmax.aibridgebrowser;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;

/** Buffers trickled ICE candidates until the remote SDP has been applied. */
public final class VoiceIceCandidateBuffer {
    private final ArrayDeque<VoiceSignalPayload.IceCandidateData> pending = new ArrayDeque<>();

    public synchronized void add(VoiceSignalPayload.IceCandidateData candidate) {
        if (candidate == null) throw new IllegalArgumentException("ice_candidate_required");
        pending.addLast(candidate);
    }

    public synchronized List<VoiceSignalPayload.IceCandidateData> drain() {
        List<VoiceSignalPayload.IceCandidateData> result = new ArrayList<>(pending);
        pending.clear();
        return result;
    }

    public synchronized void clear() { pending.clear(); }
    public synchronized int size() { return pending.size(); }
}
