package com.vidiftmax.aibridgebrowser;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/** Authenticated HTTPS client for the server-assigned AI-PHONE identity. */
public final class AiPhoneRegistryClient {
    private AiPhoneRegistryClient() {}

    public static AiPhoneIdentity fetchMyPhone(String baseUrl, String bearerToken) throws Exception {
        String normalized = AiPhoneRegistryConfig.normalizeBaseUrl(baseUrl);
        if (bearerToken == null || bearerToken.trim().isEmpty()) {
            throw new IllegalArgumentException("Token de acesso obrigatório.");
        }
        HttpURLConnection connection = (HttpURLConnection)
                new URL(normalized + "/v1/me/phone").openConnection();
        try {
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(15000);
            connection.setInstanceFollowRedirects(false);
            connection.setRequestProperty("Authorization", "Bearer " + bearerToken.trim());
            connection.setRequestProperty("Accept", "application/json");
            int status = connection.getResponseCode();
            InputStream stream = status >= 200 && status < 300
                    ? connection.getInputStream() : connection.getErrorStream();
            String body = stream == null ? "" : readFully(stream);
            if (status != HttpURLConnection.HTTP_OK) {
                if (status == 401 || status == 403) {
                    throw new SecurityException("Acesso não autorizado. Confira a credencial configurada.");
                }
                if (status == 404) throw new IllegalStateException("Endpoint de cadastro não encontrado no servidor.");
                throw new IllegalStateException("Servidor respondeu HTTP " + status + ".");
            }
            JSONObject root = new JSONObject(body);
            JSONObject phone = root.getJSONObject("phone");
            AiPhoneIdentity identity = AiPhoneIdentity.fromRegistryRecord(
                    phone.optString("aiId", null),
                    phone.optString("displayName", null),
                    phone.optString("provider", null),
                    phone.optString("status", null),
                    phone.optString("displayNumber", null),
                    phone.optString("serial", null));
            if (identity.getStatus() != AiPhoneIdentity.Status.ACTIVE) {
                throw new SecurityException("Esta identidade não está ativa no registro.");
            }
            return identity;
        } finally {
            connection.disconnect();
        }
    }

    private static String readFully(InputStream input) throws Exception {
        try (InputStream in = input; ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[2048];
            int count;
            while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        }
    }
}
