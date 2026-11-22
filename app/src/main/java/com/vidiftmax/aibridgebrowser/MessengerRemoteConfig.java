package com.vidiftmax.aibridgebrowser;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.LinkedHashSet;
import java.util.Set;

/** Validation and parsing rules for the authenticated Messenger HTTP connection. */
public final class MessengerRemoteConfig {
    private MessengerRemoteConfig() { }

    public static String normalizeBaseUrl(String value) {
        if (value == null || value.trim().isEmpty()) throw new IllegalArgumentException("server_url_required");
        try {
            URI uri = new URI(value.trim());
            if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost() == null
                    || uri.getUserInfo() != null || uri.getQuery() != null || uri.getFragment() != null)
                throw new IllegalArgumentException("https_server_url_required");
            String result = value.trim();
            while (result.endsWith("/")) result = result.substring(0, result.length() - 1);
            return result;
        } catch (URISyntaxException invalid) {
            throw new IllegalArgumentException("invalid_server_url");
        }
    }

    public static String validateAiId(String value) {
        if (value == null || !value.trim().matches("AI-[A-Z0-9][A-Z0-9-]{1,62}"))
            throw new IllegalArgumentException("invalid_ai_id");
        return value.trim();
    }

    public static Set<String> parseMemberIds(String value, String ownAiId) {
        String own = validateAiId(ownAiId);
        if (value == null || value.trim().isEmpty()) throw new IllegalArgumentException("members_required");
        Set<String> ids = new LinkedHashSet<>();
        ids.add(own);
        String[] parts = value.split(",", -1);
        for (String part : parts) {
            String candidate = part.trim();
            if (candidate.isEmpty()) throw new IllegalArgumentException("empty_member_id");
            ids.add(validateAiId(candidate));
        }
        if (ids.size() < 2 || ids.size() > 20) throw new IllegalArgumentException("member_count_out_of_range");
        return ids;
    }
}
