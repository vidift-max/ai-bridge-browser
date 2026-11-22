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

    public JSONObject getMyPhone() throws Exception { return request("GET", "/v1/me/phone", null).getJSONObject("phone"); }

    public JSONObject createConversation(String conversationId, JSONArray memberAiIds, String kind) throws Exception {
        JSONObject body = new JSONObject();
        body.put("conversationId", conversationId);
        body.put("memberAiIds", memberAiIds);
        body.put("kind", kind);
        return request("POST", "/v1/conversations", body).getJSONObject("conversation");
    }

    public JSONObject sendMessage(String conversationId, JSONArray recipients, String bodyText) throws Exception {
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
