package com.vidiftmax.aibridgebrowser;

import java.net.URI;
import java.net.URISyntaxException;

/** Pure validation for the remote AI-PHONE registry connection settings. */
public final class AiPhoneRegistryConfig {
    private AiPhoneRegistryConfig() { }

    public static String normalizeBaseUrl(String value) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException("Endereço do servidor obrigatório.");
        }
        String candidate = value.trim();
        final URI uri;
        try {
            uri = new URI(candidate);
        } catch (URISyntaxException invalid) {
            throw new IllegalArgumentException("Endereço do servidor inválido.");
        }
        if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost() == null
                || uri.getUserInfo() != null || uri.getQuery() != null || uri.getFragment() != null) {
            throw new IllegalArgumentException("Use um endereço HTTPS válido, sem usuário, senha ou parâmetros.");
        }
        String normalized = candidate;
        while (normalized.endsWith("/")) normalized = normalized.substring(0, normalized.length() - 1);
        return normalized;
    }

    public static String validateAiId(String value) {
        if (value == null || !value.trim().matches("AI-[A-Z0-9][A-Z0-9-]{1,62}")) {
            throw new IllegalArgumentException("AI_ID inválido. Exemplo: AI-GPT6.");
        }
        return value.trim();
    }
}
