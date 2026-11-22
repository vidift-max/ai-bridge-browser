package com.vidiftmax.aibridgebrowser;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

/** Synchronous HTTPS Messenger API client. Call only from a worker thread. */
public final class MessengerHttpClient {
    private final String baseUrl;
    private final String aiId;
    private final String token;

    public MessengerHttpClient(String baseUrl, String aiId, String token) {
        this.baseUrl = MessengerRemoteConfig.normalizeBaseUrl(baseUrl);
        this.aiId = MessengerRemoteConfig.validateAiId(aiId);
        if (token == null || token.trim().isEmpty()) throw new IllegalArgumentException("bearer_token_required");
        this.token = token.trim();
    }

    public JSONObject getMyIdentity() throws Exception { return request("GET", "/v1/me/identity", null).getJSONObject("identity"); }

    public JSONObject createConversation(String conversationId, JSONArray memberAiIds, String kind) throws Exception {
        if (conversationId == null || conversationId.trim().isEmpty() || conversationId.length() > 200)
            throw new IllegalArgumentException("invalid_conversation_id");
        if (!"PRIVATE".equals(kind) && !"GROUP".equals(kind))
            throw new IllegalArgumentException("invalid_conversation_kind");
        if (memberAiIds == null || memberAiIds.length() < 2 || memberAiIds.length() > 20)
            throw new IllegalArgumentException("invalid_member_count");
        boolean includesSelf = false;
        java.util.HashSet<String> unique = new java.util.HashSet<>();
        for (int i=0;i<memberAiIds.length();i++) {
            String id = MessengerRemoteConfig.validateAiId(memberAiIds.optString(i, ""));
            if (!unique.add(id)) throw new IllegalArgumentException("duplicate_member_id");
            if (aiId.equals(id)) includesSelf = true;
        }
        if (!includesSelf || ("PRIVATE".equals(kind) && memberAiIds.length() != 2))
            throw new IllegalArgumentException("invalid_conversation_members");
        JSONObject body = new JSONObject();
        body.put("conversationId", conversationId);
        body.put("memberAiIds", memberAiIds);
        body.put("kind", kind);
        return request("POST", "/v1/conversations", body).getJSONObject("conversation");
    }

    public JSONObject sendMessage(String conversationId, JSONArray recipients, String bodyText) throws Exception {
        if (conversationId == null || conversationId.trim().isEmpty() || conversationId.length() > 200)
            throw new IllegalArgumentException("invalid_conversation_id");
        if (bodyText == null || bodyText.trim().isEmpty() || bodyText.length() > 5000)
            throw new IllegalArgumentException("invalid_message_body");
        if (recipients == null || recipients.length() < 1)
            throw new IllegalArgumentException("message_recipients_required");
        java.util.HashSet<String> uniqueRecipients = new java.util.HashSet<>();
        for (int i=0;i<recipients.length();i++) {
            String id = MessengerRemoteConfig.validateAiId(recipients.optString(i, ""));
            if (aiId.equals(id) || !uniqueRecipients.add(id))
                throw new IllegalArgumentException("invalid_message_recipient");
        }
        JSONObject body = new JSONObject();
        body.put("messageId", UUID.randomUUID().toString());
        body.put("conversationId", conversationId);
        body.put("senderAiId", aiId);
        body.put("recipientAiIds", recipients);
        body.put("body", bodyText);
        body.put("clientRequestId", UUID.randomUUID().toString());
        return request("POST", "/v1/messages", body);
    }

    public JSONArray fetchPending(String conversationId, int afterSequence, int limit) throws Exception {
        String path = "/v1/conversations/" + encodePath(conversationId)
                + "/messages?after=" + Math.max(0, afterSequence) + "&limit=" + Math.max(1, Math.min(100, limit));
        return request("GET", path, null).getJSONArray("messages");
    }

    public JSONObject acknowledge(String messageId) throws Exception {
        return request("POST", "/v1/messages/" + encodePath(messageId) + "/ack", new JSONObject());
    }

    public JSONArray listAudioAttachments(String messageId) throws Exception {
        if (messageId == null || messageId.trim().isEmpty()) throw new IllegalArgumentException("message_id_required");
        return request("GET", "/v1/messages/" + encodePath(messageId) + "/audio", null)
                .getJSONArray("attachments");
    }

    public JSONObject uploadAudio(String messageId, java.io.File audioFile) throws Exception {
        if (messageId == null || messageId.trim().isEmpty()) throw new IllegalArgumentException("message_id_required");
        if (audioFile == null || !audioFile.isFile() || audioFile.length() <= 0 || audioFile.length() > 5L * 1024L * 1024L)
            throw new IllegalArgumentException("invalid_audio_file");
        HttpURLConnection connection = null;
        try {
            connection = (HttpURLConnection) new URL(baseUrl + "/v1/messages/" + encodePath(messageId) + "/audio").openConnection();
            connection.setRequestMethod("POST");
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(15000);
            connection.setDoOutput(true);
            connection.setFixedLengthStreamingMode(audioFile.length());
            connection.setRequestProperty("Authorization", "Bearer " + token);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Content-Type", "audio/mp4");
            try (InputStream in = new java.io.FileInputStream(audioFile); OutputStream out = connection.getOutputStream()) {
                byte[] buffer = new byte[8192];
                int count;
                while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
            }
            return readJsonResponse(connection);
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    public java.io.File downloadAudio(String messageId, String objectId, java.io.File destination) throws Exception {
        if (messageId == null || messageId.trim().isEmpty() || objectId == null || objectId.trim().isEmpty())
            throw new IllegalArgumentException("audio_reference_required");
        if (destination == null) throw new IllegalArgumentException("destination_required");
        HttpURLConnection connection = null;
        try {
            connection = (HttpURLConnection) new URL(baseUrl + "/v1/messages/" + encodePath(messageId) + "/audio/" + encodePath(objectId)).openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(15000);
            connection.setRequestProperty("Authorization", "Bearer " + token);
            connection.setRequestProperty("Accept", "application/octet-stream");
            int status = connection.getResponseCode();
            if (status < 200 || status >= 300) throw httpError(connection, status);
            java.io.File parent = destination.getParentFile();
            if (parent != null && !parent.exists() && !parent.mkdirs()) throw new java.io.IOException("audio_destination_unavailable");
            try {
                try (InputStream in = connection.getInputStream(); java.io.FileOutputStream out = new java.io.FileOutputStream(destination)) {
                    byte[] buffer = new byte[8192];
                    long total = 0;
                    int count;
                    while ((count = in.read(buffer)) != -1) {
                        total += count;
                        if (total > 5L * 1024L * 1024L) throw new java.io.IOException("audio_download_too_large");
                        out.write(buffer, 0, count);
                    }
                }
            } catch (Exception error) {
                if (destination.isFile()) destination.delete();
                throw error;
            }
            return destination;
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    private JSONObject readJsonResponse(HttpURLConnection connection) throws Exception {
        int status = connection.getResponseCode();
        InputStream stream = status >= 200 && status < 300 ? connection.getInputStream() : connection.getErrorStream();
        String response = stream == null ? "{}" : readBounded(stream);
        if (status < 200 || status >= 300) {
            String code = "http_" + status;
            try { code = new JSONObject(response).optString("error", code); } catch (Exception ignored) { }
            throw new MessengerHttpException(status, code);
        }
        return new JSONObject(response);
    }

    private Exception httpError(HttpURLConnection connection, int status) throws Exception {
        InputStream stream = connection.getErrorStream();
        String response = stream == null ? "{}" : readBounded(stream);
        String code = "http_" + status;
        try { code = new JSONObject(response).optString("error", code); } catch (Exception ignored) { }
        return new MessengerHttpException(status, code);
    }

    public String getAiId() { return aiId; }

    private JSONObject request(String method, String path, JSONObject payload) throws Exception {
        HttpURLConnection connection = null;
        try {
            connection = (HttpURLConnection) new URL(baseUrl + path).openConnection();
            connection.setRequestMethod(method);
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(15000);
            connection.setUseCaches(false);
            connection.setRequestProperty("Authorization", "Bearer " + token);
            connection.setRequestProperty("Accept", "application/json");
            if (payload != null) {
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                byte[] bytes = payload.toString().getBytes(StandardCharsets.UTF_8);
                connection.setFixedLengthStreamingMode(bytes.length);
                try (OutputStream out = connection.getOutputStream()) { out.write(bytes); }
            }
            int status = connection.getResponseCode();
            InputStream stream = status >= 200 && status < 300 ? connection.getInputStream() : connection.getErrorStream();
            String response = stream == null ? "{}" : readBounded(stream);
            if (status < 200 || status >= 300) {
                String code = "http_" + status;
                try { code = new JSONObject(response).optString("error", code); } catch (Exception ignored) { }
                throw new MessengerHttpException(status, code);
            }
            return new JSONObject(response);
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    private static String readBounded(InputStream input) throws Exception {
        try (InputStream in = input; ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[2048];
            int count;
            while ((count = in.read(buffer)) != -1) {
                out.write(buffer, 0, count);
                if (out.size() > 65536) throw new IllegalStateException("messenger_response_too_large");
            }
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        }
    }

    private static String encodePath(String value) {
        try { return java.net.URLEncoder.encode(value, "UTF-8").replace("+", "%20"); }
        catch (java.io.UnsupportedEncodingException impossible) { throw new IllegalStateException("UTF-8 unavailable", impossible); }
    }

    public static final class MessengerHttpException extends Exception {
        private final int statusCode;
        private final String errorCode;
        MessengerHttpException(int statusCode, String errorCode) {
            super("Messenger HTTP " + statusCode + ": " + errorCode);
            this.statusCode = statusCode;
            this.errorCode = errorCode;
        }
        public int getStatusCode() { return statusCode; }
        public String getErrorCode() { return errorCode; }
    }
}
