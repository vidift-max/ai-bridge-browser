package com.vidiftmax.aibridgebrowser;

import java.net.URI;

/** Validation for the user-configured AI-PHONE registry origin. */
public final class AiPhoneRegistryConfig {
    private AiPhoneRegistryConfig() {}

    public static String normalizeBaseUrl(String value) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException("Endereço do servidor obrigatório.");
        }
        String candidate = value.trim();
        final URI uri;
        try { uri = URI.create(candidate); }
        catch (RuntimeException invalid) {
            throw new IllegalArgumentException("Endereço do servidor inválido.");
        }
        if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost() == null ||
                uri.getUserInfo() != null || uri.getQuery() != null || uri.getFragment() != null) {
            throw new IllegalArgumentException("Use um endereço HTTPS válido, sem usuário, senha ou parâmetros.");
        }
        String path = uri.getRawPath();
        if (path != null && !path.isEmpty() && !"/".equals(path)) {
            throw new IllegalArgumentException("Informe somente o endereço-base do servidor, sem caminho.");
        }
        int port = uri.getPort();
        if (port != -1 && (port < 1 || port > 65535)) {
            throw new IllegalArgumentException("Porta do servidor inválida.");
        }
        return "https://" + uri.getHost().toLowerCase() + (port == -1 ? "" : ":" + port);
    }
}
