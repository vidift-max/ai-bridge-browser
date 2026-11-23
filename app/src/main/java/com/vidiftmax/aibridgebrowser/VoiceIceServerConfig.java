package com.vidiftmax.aibridgebrowser;

import org.json.JSONArray;
import org.json.JSONObject;
import org.webrtc.PeerConnection;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Parses an operator-provided ICE server JSON document.
 *
 * Secrets are accepted only for TURN entries and are never logged. No public
 * STUN/TURN endpoint is selected implicitly.
 *
 * Format:
 * [{"url":"stun:stun.example.invalid"},
 *  {"url":"turn:turn.example.invalid:3478?transport=udp",
 *   "username":"ephemeral-user","password":"ephemeral-password"}]
 */
public final class VoiceIceServerConfig {
    private static final int MAX_SERVERS = 4;
    private static final int MAX_URL_CHARS = 512;
    private static final int MAX_CREDENTIAL_CHARS = 512;

    private VoiceIceServerConfig() {}

    public static List<PeerConnection.IceServer> parse(String json) throws Exception {
        if (json == null || json.trim().isEmpty()) return Collections.emptyList();
        JSONArray array = new JSONArray(json);
        if (array.length() > MAX_SERVERS) throw new IllegalArgumentException("too_many_ice_servers");

        List<PeerConnection.IceServer> result = new ArrayList<>();
        for (int i = 0; i < array.length(); i++) {
            JSONObject item = array.optJSONObject(i);
            if (item == null) throw new IllegalArgumentException("ice_server_object_required");
            String url = item.optString("url", "").trim();
            validateUrl(url);
            String username = item.optString("username", "").trim();
            String password = item.optString("password", "").trim();
            boolean turn = url.regionMatches(true, 0, "turn:", 0, 5)
                    || url.regionMatches(true, 0, "turns:", 0, 6);
            if (turn) {
                if (username.isEmpty() || password.isEmpty())
                    throw new IllegalArgumentException("turn_credentials_required");
                validateCredential(username, "turn_username");
                validateCredential(password, "turn_password");
                result.add(PeerConnection.IceServer.builder(url)
                        .setUsername(username).setPassword(password).createIceServer());
            } else {
                if (!username.isEmpty() || !password.isEmpty())
                    throw new IllegalArgumentException("stun_credentials_not_allowed");
                result.add(PeerConnection.IceServer.builder(url).createIceServer());
            }
        }
        return Collections.unmodifiableList(result);
    }

    private static void validateUrl(String url) {
        if (url.isEmpty() || url.length() > MAX_URL_CHARS)
            throw new IllegalArgumentException("ice_url_invalid");
        boolean valid = url.regionMatches(true, 0, "stun:", 0, 5)
                || url.regionMatches(true, 0, "stuns:", 0, 6)
                || url.regionMatches(true, 0, "turn:", 0, 5)
                || url.regionMatches(true, 0, "turns:", 0, 6);
        if (!valid || url.indexOf(' ') >= 0 || url.indexOf('\\n') >= 0 || url.indexOf('\\r') >= 0)
            throw new IllegalArgumentException("ice_url_scheme_invalid");
    }

    private static void validateCredential(String value, String code) {
        if (value.length() > MAX_CREDENTIAL_CHARS)
            throw new IllegalArgumentException(code + "_too_long");
    }
}
