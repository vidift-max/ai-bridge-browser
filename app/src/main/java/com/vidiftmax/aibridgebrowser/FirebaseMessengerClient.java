package com.vidiftmax.aibridgebrowser;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Iterator;
import java.util.UUID;

/**
 * No-server Messenger transport using Firebase Realtime Database REST + anonymous Auth.
 * The Firebase Web API key is configuration, not an admin credential.
 */
public final class FirebaseMessengerClient {
    private static final String AUTH_PREFS = "ai_messenger_firebase_auth_v1";
    private final Context context;
    private final String databaseUrl;
    private final String apiKey;
    private final String aiId;

    public FirebaseMessengerClient(Context context, String databaseUrl, String apiKey, String aiId) {
        if (context == null) throw new IllegalArgumentException("context_required");
        this.context = context.getApplicationContext();
        this.databaseUrl = normalizeDatabaseUrl(databaseUrl);
        if (apiKey == null || apiKey.trim().isEmpty()) throw new IllegalArgumentException("firebase_api_key_required");
        this.apiKey = apiKey.trim();
        this.aiId = MessengerRemoteConfig.validateAiId(aiId);
    }

    public String getLocalUid() throws Exception { return session().uid; }

    public JSONObject getMyIdentity() throws Exception {
        JSONObject identity = databaseRequest("GET", "/messenger/identities/" + path(aiId), null);
        if (identity == null || !aiId.equals(identity.optString("aiId", ""))) {
            throw new IllegalStateException("firebase_identity_not_provisioned");
        }
        String uid = identity.optString("uid", "");
        if (!uid.equals(session().uid)) throw new IllegalStateException("firebase_identity_uid_mismatch");
        return new JSONObject().put("aiId", aiId).put("uid", uid).put("transport", "firebase_rtdb");
    }

    public JSONObject getConversation(String conversationId) throws Exception {
        if (conversationId == null || conversationId.trim().isEmpty()) throw new IllegalArgumentException("conversation_id_required");
        return databaseRequest("GET", "/messenger/conversations/" + path(conversationId), null);
    }

    public JSONObject createGroupInvite(String conversationId, long expiresAtEpochMs) throws Exception {
        if (conversationId == null || conversationId.trim().isEmpty()) throw new IllegalArgumentException("conversation_id_required");
        if (expiresAtEpochMs <= System.currentTimeMillis()) throw new IllegalArgumentException("invite_expired");
        byte[] bytes = new byte[24];
        new java.security.SecureRandom().nextBytes(bytes);
        String token = android.util.Base64.encodeToString(bytes, android.util.Base64.URL_SAFE | android.util.Base64.NO_WRAP | android.util.Base64.NO_PADDING);
        String hostingUrl = context.getSharedPreferences("ai_phone_registry_config_v1", Context.MODE_PRIVATE)
                .getString("invite_hosting_url", "");
        String publicBase = MessengerRemoteConfig.normalizeInviteHostingUrl(hostingUrl);
        JSONObject invite = new JSONObject()
                .put("conversationId", conversationId)
                .put("createdByAiId", aiId)
                .put("expiresAtEpochMs", expiresAtEpochMs);
        databaseRequest("PUT", "/messenger/invites/" + path(token), invite);
        return new JSONObject()
                .put("token", token)
                .put("conversationId", conversationId)
                .put("expiresAtEpochMs", expiresAtEpochMs)
                .put("link", publicBase + "/i/" + path(conversationId) + "/" + path(token));
    }

    public JSONObject redeemGroupInvite(String conversationId, String token) throws Exception {
        if (conversationId == null || conversationId.trim().isEmpty()) throw new IllegalArgumentException("conversation_id_required");
        if (token == null || !token.matches("[A-Za-z0-9_-]{20,64}")) throw new IllegalArgumentException("invalid_invite_token");
        JSONObject invite = databaseRequest("GET", "/messenger/invites/" + path(token), null);
        if (invite == null || !conversationId.equals(invite.optString("conversationId", "")))
            throw new IllegalArgumentException("invite_not_found");
        if (invite.optLong("expiresAtEpochMs", 0L) <= System.currentTimeMillis())
            throw new IllegalArgumentException("invite_expired");
        databaseRequest("PUT", "/messenger/invitesByAi/" + path(aiId) + "/" + path(conversationId) + "/" + path(token), trueJson());
        for (int attempt = 0; attempt < 3; attempt++) {
            ConditionalJson current = getJsonWithEtag("/messenger/conversations/" + path(conversationId));
            JSONObject room = current.body;
            JSONObject meta = room == null ? null : room.optJSONObject("meta");
            JSONObject members = room == null ? null : room.optJSONObject("members");
            if (meta == null || !"GROUP".equals(meta.optString("kind", ""))) throw new IllegalArgumentException("invite_not_group");
            int memberCount = members == null ? 0 : members.length();
            boolean alreadyMember = members != null && members.has(aiId);
            if (memberCount < 1 || (!alreadyMember && memberCount >= 20))
                throw new IllegalStateException("group_member_limit_20");
            if (alreadyMember) return new JSONObject().put("conversationId", conversationId).put("aiId", aiId).put("state", "ALREADY_MEMBER");
            JSONObject updated = new JSONObject(room.toString());
            updated.getJSONObject("members").put(aiId, true);
            updated.put("memberCount", memberCount + 1);
            try {
                putWithEtag("/messenger/conversations/" + path(conversationId), updated, current.etag);
                return new JSONObject().put("conversationId", conversationId).put("aiId", aiId).put("state", "JOINED_BY_INVITE");
            } catch (ConditionalWriteException conflict) {
                if (attempt == 2) throw conflict;
            }
        }
        throw new IllegalStateException("group_join_conflict_retry");
    }

    public JSONObject createConversation(String conversationId, JSONArray memberAiIds, String kind) throws Exception {
        if (conversationId == null || conversationId.trim().isEmpty() || conversationId.length() > 200)
            throw new IllegalArgumentException("invalid_conversation_id");
        MessengerRemoteConfig.validateConversationMemberCount(kind, memberAiIds == null ? 0 : memberAiIds.length());
        JSONObject members = new JSONObject();
        boolean self = false;
        for (int i = 0; i < memberAiIds.length(); i++) {
            String id = MessengerRemoteConfig.validateAiId(memberAiIds.optString(i, ""));
            members.put(id, true);
            self |= aiId.equals(id);
        }
        if (!self) throw new IllegalArgumentException("invalid_conversation_members");
        JSONObject root = new JSONObject();
        root.put("meta", new JSONObject()
                .put("ownerAiId", aiId)
                .put("kind", kind)
                .put("createdAtEpochMs", System.currentTimeMillis()));
        root.put("members", members);
        root.put("memberCount", memberAiIds.length());
        databaseRequest("PUT", "/messenger/conversations/" + path(conversationId), root);
        return new JSONObject().put("conversationId", conversationId)
                .put("kind", kind).put("memberAiIds", memberAiIds);
    }

    public JSONObject sendMessage(String conversationId, JSONArray recipients, String bodyText, String messageKind) throws Exception {
        MessengerRemoteConfig.validateMessageBody(bodyText);
        if (recipients == null || recipients.length() < 1) throw new IllegalArgumentException("message_recipients_required");
        JSONObject room = getConversation(conversationId);
        JSONObject recipientsObject = FirebaseMessageAdmission.validate(aiId, recipients, room);
        JSONObject message = new JSONObject()
                .put("senderAiId", aiId)
                .put("recipientAiIds", recipientsObject)
                .put("body", bodyText)
                .put("messageKind", MessengerRetentionPolicy.normalizeMessageKind(messageKind))
                .put("createdAtEpochMs", System.currentTimeMillis());
        JSONObject pushed = databaseRequest("POST",
                "/messenger/conversations/" + path(conversationId) + "/messages", message);
        String messageId = pushed == null ? "" : pushed.optString("name", "");
        if (messageId.isEmpty()) throw new IllegalStateException("firebase_message_key_missing");
        return new JSONObject()
                .put("messageId", messageId)
                .put("conversationId", conversationId)
                .put("senderAiId", aiId)
                .put("sequence", 0)
                .put("state", "QUEUED_ON_FIREBASE")
                .put("transport", "firebase_rtdb");
    }

    public JSONArray fetchPending(String conversationId, int afterSequence, int limit) throws Exception {
        String url = databaseUrl + "/messenger/conversations/" + path(conversationId)
                + "/messages.json?auth=" + encode(session().idToken)
                + "&orderBy=%22$key%22&limitToFirst=" + Math.max(1, Math.min(100, limit));
        JSONObject root = getJson(url);
        JSONArray result = new JSONArray();
        if (root == null) return result;
        Iterator<String> keys = root.keys();
        while (keys.hasNext()) {
            String key = keys.next();
            JSONObject message = root.optJSONObject(key);
            if (message == null) continue;
            JSONObject recipients = message.optJSONObject("recipientAiIds");
            if (aiId.equals(message.optString("senderAiId")) ||
                    (recipients != null && recipients.optBoolean(aiId, false))) {
                result.put(new JSONObject()
                        .put("messageId", key)
                        .put("conversationId", conversationId)
                        .put("senderAiId", message.optString("senderAiId", "AI"))
                        .put("body", message.optString("body", ""))
                        .put("messageKind", message.optString("messageKind", MessengerRetentionPolicy.MESSAGE_NORMAL))
                        .put("createdAtEpochMs", message.optLong("createdAtEpochMs", System.currentTimeMillis()))
                        .put("sequence", 0));
            }
        }
        return result;
    }

    public JSONObject acknowledge(String conversationId, String messageId) throws Exception {
        if (conversationId == null || messageId == null || conversationId.isEmpty() || messageId.isEmpty())
            throw new IllegalArgumentException("ack_reference_required");
        databaseRequest("PUT", "/messenger/conversations/" + path(conversationId) + "/acks/" + path(messageId)
                + "/" + path(aiId), trueJson());
        return new JSONObject().put("state", "ACKNOWLEDGED").put("messageId", messageId);
    }

    private Session session() throws Exception {
        synchronized (AUTH_PREFS.intern()) {
            SharedPreferences p = context.getSharedPreferences(AUTH_PREFS, Context.MODE_PRIVATE);
            long expiresAt = p.getLong("expires_at_ms", 0L);
            String idToken = p.getString("id_token", "");
            String refreshToken = p.getString("refresh_token", "");
            String uid = p.getString("uid", "");
            if (!idToken.isEmpty() && !uid.isEmpty() && expiresAt > System.currentTimeMillis() + 60000L)
                return new Session(idToken, refreshToken, uid);
            if (!refreshToken.isEmpty()) {
                try {
                    JSONObject refreshed = authPost("https://securetoken.googleapis.com/v1/token?key=" + encode(apiKey),
                            "grant_type=refresh_token&refresh_token=" + encode(refreshToken), false);
                    Session s = new Session(refreshed.getString("id_token"),
                            refreshed.optString("refresh_token", refreshToken),
                            refreshed.getString("user_id"));
                    saveSession(s, refreshed.optLong("expires_in", 3600));
                    return s;
                } catch (Exception ignored) {
                    p.edit().clear().apply();
                }
            }
            JSONObject created = authPost("https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=" + encode(apiKey),
                    new JSONObject().put("returnSecureToken", true).toString(), true);
            Session s = new Session(created.getString("idToken"), created.getString("refreshToken"),
                    created.getString("localId"));
            saveSession(s, created.optLong("expiresIn", 3600));
            return s;
        }
    }

    private void saveSession(Session s, long expiresInSeconds) {
        context.getSharedPreferences(AUTH_PREFS, Context.MODE_PRIVATE).edit()
                .putString("id_token", s.idToken)
                .putString("refresh_token", s.refreshToken)
                .putString("uid", s.uid)
                .putLong("expires_at_ms", System.currentTimeMillis() + Math.max(60, expiresInSeconds - 60) * 1000L)
                .apply();
    }

    private JSONObject authPost(String url, String body, boolean json) throws Exception {
        HttpURLConnection c = null;
        try {
            c = (HttpURLConnection) new URL(url).openConnection();
            c.setRequestMethod("POST"); c.setConnectTimeout(10000); c.setReadTimeout(15000); c.setDoOutput(true);
            c.setRequestProperty("Content-Type", json ? "application/json" : "application/x-www-form-urlencoded");
            byte[] data = body.getBytes(StandardCharsets.UTF_8);
            c.setFixedLengthStreamingMode(data.length);
            try (OutputStream out = c.getOutputStream()) { out.write(data); }
            return readJson(c);
        } finally { if (c != null) c.disconnect(); }
    }

    private JSONObject databaseRequest(String method, String path, Object body) throws Exception {
        Session s = session();
        String url = databaseUrl + path + ".json?auth=" + encode(s.idToken);
        HttpURLConnection c = null;
        try {
            c = (HttpURLConnection) new URL(url).openConnection();
            c.setRequestMethod(method); c.setConnectTimeout(10000); c.setReadTimeout(15000);
            c.setRequestProperty("Accept", "application/json");
            if (body != null) {
                c.setDoOutput(true); c.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                byte[] data = (body instanceof JSONObject || body instanceof JSONArray ? body.toString() : String.valueOf(body))
                        .getBytes(StandardCharsets.UTF_8);
                c.setFixedLengthStreamingMode(data.length);
                try (OutputStream out = c.getOutputStream()) { out.write(data); }
            }
            return readJson(c);
        } finally { if (c != null) c.disconnect(); }
    }

    private ConditionalJson getJsonWithEtag(String path) throws Exception {
        Session s = session();
        HttpURLConnection c = null;
        try {
            c = (HttpURLConnection) new URL(databaseUrl + path + ".json?auth=" + encode(s.idToken)).openConnection();
            c.setRequestMethod("GET");
            c.setConnectTimeout(10000); c.setReadTimeout(15000);
            c.setRequestProperty("Accept", "application/json");
            c.setRequestProperty("X-Firebase-ETag", "true");
            JSONObject body = readJson(c);
            String etag = c.getHeaderField("ETag");
            if (etag == null || etag.trim().isEmpty()) throw new IllegalStateException("firebase_etag_missing");
            return new ConditionalJson(body, etag);
        } finally { if (c != null) c.disconnect(); }
    }

    private void putWithEtag(String path, JSONObject body, String etag) throws Exception {
        Session s = session();
        HttpURLConnection c = null;
        try {
            c = (HttpURLConnection) new URL(databaseUrl + path + ".json?auth=" + encode(s.idToken)).openConnection();
            c.setRequestMethod("PUT");
            c.setConnectTimeout(10000); c.setReadTimeout(15000);
            c.setDoOutput(true);
            c.setRequestProperty("Accept", "application/json");
            c.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            c.setRequestProperty("if-match", etag);
            byte[] data = body.toString().getBytes(StandardCharsets.UTF_8);
            c.setFixedLengthStreamingMode(data.length);
            try (OutputStream out = c.getOutputStream()) { out.write(data); }
            int status = c.getResponseCode();
            String response = readBounded(status >= 200 && status < 300 ? c.getInputStream() : c.getErrorStream());
            if (status == 412) throw new ConditionalWriteException("firebase_etag_conflict");
            if (status < 200 || status >= 300) throw new IllegalStateException("firebase_http_" + status + ":" + response);
        } finally { if (c != null) c.disconnect(); }
    }

    private JSONObject getJson(String url) throws Exception {
        HttpURLConnection c = null;
        try {
            c = (HttpURLConnection) new URL(url).openConnection();
            c.setRequestMethod("GET"); c.setConnectTimeout(10000); c.setReadTimeout(15000);
            return readJson(c);
        } finally { if (c != null) c.disconnect(); }
    }

    private static JSONObject readJson(HttpURLConnection c) throws Exception {
        int status = c.getResponseCode();
        InputStream in = status >= 200 && status < 300 ? c.getInputStream() : c.getErrorStream();
        String text = readBounded(in);
        if (status < 200 || status >= 300) throw new IllegalStateException("firebase_http_" + status + ":" + text);
        if (text == null || text.trim().isEmpty() || "null".equals(text.trim())) return null;
        return new JSONObject(text);
    }

    private static String readBounded(InputStream in) throws Exception {
        if (in == null) return "";
        try (InputStream input = in; ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] b = new byte[4096]; int n;
            while ((n = input.read(b)) != -1) { out.write(b, 0, n); if (out.size() > 65536) throw new IllegalStateException("firebase_response_too_large"); }
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }

    private static Boolean trueJson() { return Boolean.TRUE; }
    private static String path(String value) throws Exception { return encode(value.replace("~","%7E")); }
    private static String encode(String value) throws Exception { return URLEncoder.encode(value, "UTF-8").replace("+", "%20"); }

    static boolean isFirebaseDatabaseUrl(String value) {
        try { URI uri = new URI(value); String host = uri.getHost(); return "https".equalsIgnoreCase(uri.getScheme()) && host != null && (host.equals("firebaseio.com") || host.endsWith(".firebaseio.com") || host.equals("firebasedatabase.app") || host.endsWith(".firebasedatabase.app")) && uri.getQuery() == null && uri.getFragment() == null; }
        catch (Exception ignored) { return false; }
    }

    static String normalizeDatabaseUrl(String value) {
        if (value == null || value.trim().isEmpty()) throw new IllegalArgumentException("firebase_database_url_required");
        try {
            URI uri = new URI(value.trim());
            String host = uri.getHost();
            if (!"https".equalsIgnoreCase(uri.getScheme()) || host == null ||
                    !(host.equals("firebaseio.com") || host.endsWith(".firebaseio.com") || host.equals("firebasedatabase.app") || host.endsWith(".firebasedatabase.app")) ||
                    uri.getQuery() != null || uri.getFragment() != null)
                throw new IllegalArgumentException("firebase_database_url_invalid");
            String result = value.trim();
            while (result.endsWith("/")) result = result.substring(0, result.length()-1);
            return result;
        } catch (Exception e) {
            if (e instanceof IllegalArgumentException) throw (IllegalArgumentException)e;
            throw new IllegalArgumentException("firebase_database_url_invalid");
        }
    }

    private static final class ConditionalJson {
        final JSONObject body; final String etag;
        ConditionalJson(JSONObject body, String etag) { this.body = body; this.etag = etag; }
    }

    private static final class ConditionalWriteException extends Exception {
        ConditionalWriteException(String message) { super(message); }
    }

    private static final class Session {
        final String idToken, refreshToken, uid;
        Session(String idToken, String refreshToken, String uid) {
            this.idToken=idToken; this.refreshToken=refreshToken; this.uid=uid;
        }
    }
}
