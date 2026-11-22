package com.vidiftmax.aibridgebrowser;

import android.os.Handler;
import android.os.Looper;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Authenticated HTTPS client for the AI-PHONE self-registration endpoint. */
public final class AiPhoneRegistryClient {
    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private final String baseUrl;
    private final String aiId;
    private final String bearerToken;

    public interface Callback {
        void onSuccess(AiPhoneIdentity identity);
        void onError(String safeMessage);
    }

    public AiPhoneRegistryClient(String baseUrl, String aiId, String bearerToken) {
        this.baseUrl = AiPhoneRegistryConfig.normalizeBaseUrl(baseUrl);
        this.aiId = AiPhoneRegistryConfig.validateAiId(aiId);
        if (bearerToken == null || bearerToken.trim().isEmpty()) {
            throw new IllegalArgumentException("Token de autenticação obrigatório.");
        }
        this.bearerToken = bearerToken.trim();
    }

    public void register(Callback callback) {
        if (callback == null) throw new IllegalArgumentException("callback_required");
        EXECUTOR.execute(() -> {
            HttpURLConnection connection = null;
            try {
                URL endpoint = new URL(baseUrl + "/v1/me/phone");
                connection = (HttpURLConnection) endpoint.openConnection();
                connection.setRequestMethod("GET");
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(10000);
                connection.setUseCaches(false);
                connection.setRequestProperty("Authorization", "Bearer " + bearerToken);
                connection.setRequestProperty("Accept", "application/json");
                int status = connection.getResponseCode();
                if (status != HttpURLConnection.HTTP_OK) {
                    String reason = status == 401 ? "Token não autenticado."
                            : status == 403 ? "Identidade sem autorização."
                            : status == 429 ? "Muitas tentativas. Aguarde e tente novamente."
                            : status >= 500 ? "Servidor temporariamente indisponível."
                            : "Cadastro não concluído (HTTP " + status + ").";
                    throw new RegistryException(reason);
                }
                String body = readFully(connection.getInputStream());
                JSONObject root = new JSONObject(body);
                JSONObject phone = root.getJSONObject("phone");
                AiPhoneIdentity identity = AiPhoneIdentity.fromRegistryRecord(
                        phone.optString("aiId", null),
                        phone.optString("displayName", null),
                        phone.optString("provider", null),
                        phone.optString("status", null),
                        phone.optString("displayNumber", null),
                        phone.optString("serial", null));
                if (!aiId.equals(identity.getAiId())) {
                    throw new RegistryException("O servidor retornou outra identidade. Registro não exibido.");
                }
                MAIN.post(() -> callback.onSuccess(identity));
            } catch (RegistryException error) {
                MAIN.post(() -> callback.onError(error.getMessage()));
            } catch (Exception error) {
                MAIN.post(() -> callback.onError(
                        "Não foi possível consultar o cadastro. Verifique a conexão e o endereço do servidor."));
            } finally {
                if (connection != null) connection.disconnect();
            }
        });
    }

    private static String readFully(InputStream input) throws Exception {
        try (InputStream in = input; ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[2048];
            int count;
            while ((count = in.read(buffer)) != -1) {
                out.write(buffer, 0, count);
                if (out.size() > 32768) throw new RegistryException("Resposta do servidor muito grande.");
            }
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        }
    }

    private static final class RegistryException extends Exception {
        RegistryException(String message) { super(message); }
    }
}
