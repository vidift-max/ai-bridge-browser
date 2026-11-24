package com.vidiftmax.aibridgebrowser;

import org.json.JSONException;
import org.json.JSONObject;

/** Validated JSON payloads shared by the REST signaling client and WebRTC engine. */
public final class VoiceSignalPayload {
    public static final int MAX_SDP_CHARS = 18000;
    public static final int MAX_CANDIDATE_CHARS = 4096;

    private VoiceSignalPayload() { }

    public static JSONObject sessionDescription(String type, String sdp) throws JSONException {
        if (!"offer".equals(type) && !"answer".equals(type))
            throw new IllegalArgumentException("invalid_voice_sdp_type");
        if (sdp == null || sdp.trim().isEmpty() || sdp.length() > MAX_SDP_CHARS)
            throw new IllegalArgumentException("invalid_voice_sdp");
        return new JSONObject().put("type", type).put("sdp", sdp);
    }

    public static JSONObject iceCandidate(String candidate, String sdpMid,
                                          int sdpMLineIndex, String usernameFragment)
            throws JSONException {
        if (candidate == null || candidate.trim().isEmpty()
                || candidate.length() > MAX_CANDIDATE_CHARS)
            throw new IllegalArgumentException("invalid_ice_candidate");
        if (sdpMLineIndex < 0 || sdpMLineIndex > 65535)
            throw new IllegalArgumentException("invalid_ice_mline_index");
        JSONObject result = new JSONObject().put("candidate", candidate)
                .put("sdpMLineIndex", sdpMLineIndex);
        if (sdpMid != null && !sdpMid.isEmpty()) {
            if (sdpMid.length() > 256) throw new IllegalArgumentException("invalid_ice_sdp_mid");
            result.put("sdpMid", sdpMid);
        }
        if (usernameFragment != null && !usernameFragment.isEmpty()) {
            if (usernameFragment.length() > 256)
                throw new IllegalArgumentException("invalid_ice_username_fragment");
            result.put("usernameFragment", usernameFragment);
        }
        return result;
    }

    public static JSONObject iceComplete() throws JSONException {
        return new JSONObject();
    }

    public static IceCandidateData readIceCandidate(JSONObject payload) {
        if (payload == null) throw new IllegalArgumentException("invalid_ice_candidate");
        String candidate = payload.optString("candidate", "");
        String sdpMid = payload.isNull("sdpMid") ? null : payload.optString("sdpMid", null);
        int line = payload.optInt("sdpMLineIndex", -1);
        String usernameFragment = payload.isNull("usernameFragment")
                ? null : payload.optString("usernameFragment", null);
        if (candidate.trim().isEmpty() || candidate.length() > MAX_CANDIDATE_CHARS
                || line < 0 || line > 65535
                || (sdpMid != null && sdpMid.length() > 256)
                || (usernameFragment != null && usernameFragment.length() > 256))
            throw new IllegalArgumentException("invalid_ice_candidate");
        return new IceCandidateData(candidate, sdpMid, line, usernameFragment);
    }

    public static final class IceCandidateData {
        public final String candidate;
        public final String sdpMid;
        public final int sdpMLineIndex;
        public final String usernameFragment;

        private IceCandidateData(String candidate, String sdpMid, int sdpMLineIndex,
                                 String usernameFragment) {
            this.candidate = candidate;
            this.sdpMid = sdpMid;
            this.sdpMLineIndex = sdpMLineIndex;
            this.usernameFragment = usernameFragment;
        }
    }
}
