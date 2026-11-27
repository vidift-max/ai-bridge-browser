package com.vidiftmax.aibridgebrowser;

import java.net.URI;
import java.util.Locale;

/** Strict parser for public AI Messenger group-invitation deep links. */
final class InviteLinkParser {
    static final class Invite {
        final String conversationId;
        final String token;

        Invite(String conversationId, String token) {
            this.conversationId = conversationId;
            this.token = token;
        }
    }

    private InviteLinkParser() {}

    static Invite parse(String value) {
        if (value == null || value.trim().isEmpty() || !value.equals(value.trim())) return null;
        try {
            URI uri = new URI(value);
            if (uri.isOpaque() || uri.getRawUserInfo() != null || uri.getPort() != -1
                    || uri.getRawQuery() != null || uri.getRawFragment() != null) return null;

            String scheme = uri.getScheme();
            String host = uri.getHost();
            String rawPath = uri.getRawPath();
            if (scheme == null || host == null || rawPath == null || rawPath.indexOf('%') >= 0) return null;

            String[] parts;
            if ("aibridge".equalsIgnoreCase(scheme) && "invite".equalsIgnoreCase(host)) {
                parts = rawPath.split("/", -1);
                if (parts.length != 3 || !parts[0].isEmpty()) return null;
                return valid(parts[1], parts[2]);
            }

            String normalizedHost = host.toLowerCase(Locale.ROOT);
            if (!"https".equalsIgnoreCase(scheme)
                    || !normalizedHost.matches("[a-z0-9-]+(?:[.][a-z0-9-]+)*[.]web[.]app")) return null;

            parts = rawPath.split("/", -1);
            if (parts.length != 4 || !parts[0].isEmpty() || !"i".equals(parts[1])) return null;
            return valid(parts[2], parts[3]);
        } catch (Exception ignored) {
            return null;
        }
    }

    private static Invite valid(String conversationId, String token) {
        if (conversationId == null || !conversationId.matches("[A-Za-z0-9_-]{1,128}")) return null;
        if (token == null || !token.matches("[A-Za-z0-9_-]{20,64}")) return null;
        return new Invite(conversationId, token);
    }
}
