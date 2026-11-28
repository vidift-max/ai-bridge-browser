package com.vidiftmax.aibridgebrowser;

import java.net.URI;
import java.net.URISyntaxException;

/** Strict URL policy for browser navigation. Only HTTPS origins are permitted. */
final class BrowserNavigationPolicy {
    private BrowserNavigationPolicy() {}

    static boolean isAllowedWebUrl(String value) {
        if (value == null || value.isEmpty() || !value.equals(value.trim())) return false;
        try {
            URI uri = new URI(value);
            if (uri.isOpaque()) return false;
            if (!"https".equalsIgnoreCase(uri.getScheme())) return false;
            if (uri.getRawUserInfo() != null) return false;
            String host = uri.getHost();
            if (host == null || host.isEmpty()) return false;
            int port = uri.getPort();
            return port == -1 || (port >= 1 && port <= 65535);
        } catch (URISyntaxException error) {
            return false;
        }
    }

    static String normalizeUrl(String value, String fallbackUrl) {
        String candidate = value == null ? "" : value.trim();
        if (candidate.isEmpty()) return fallbackUrl;
        if (!candidate.contains("://")) candidate = "https://" + candidate;
        return isAllowedWebUrl(candidate) ? candidate : fallbackUrl;
    }
}
