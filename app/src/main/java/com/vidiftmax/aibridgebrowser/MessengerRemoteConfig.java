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

    public static String normalizeInviteHostingUrl(String value) {
        if (value == null || value.trim().isEmpty()) throw new IllegalArgumentException("firebase_invite_hosting_url_required");
        try {
            URI uri = new URI(value.trim());
            String host = uri.getHost();
            if (!"https".equalsIgnoreCase(uri.getScheme()) || host == null
                    || !host.toLowerCase(java.util.Locale.ROOT).matches("[a-z0-9-]+(?:\\.[a-z0-9-]+)*\\.web\\.app")
                    || (uri.getRawPath() != null && !uri.getRawPath().isEmpty() && !"/".equals(uri.getRawPath()))
                    || uri.getRawUserInfo() != null || uri.getPort() != -1
                    || uri.getRawQuery() != null || uri.getRawFragment() != null)
                throw new IllegalArgumentException("firebase_invite_hosting_url_invalid");
            return "https://" + host.toLowerCase(java.util.Locale.ROOT);
        } catch (java.net.URISyntaxException invalid) {
            throw new IllegalArgumentException("firebase_invite_hosting_url_invalid");
        }
    }

    public static String validateAiId(String value) {
        if (value == null || !value.trim().matches("AI-[A-Z0-9][A-Z0-9-]{0,62}"))
            throw new IllegalArgumentException("invalid_ai_id");
        return value.trim();
    }

    public static void validateConversationMemberCount(String kind, int memberCount) {
        if (!"PRIVATE".equals(kind) && !"GROUP".equals(kind))
            throw new IllegalArgumentException("invalid_conversation_kind");
        if ("PRIVATE".equals(kind) && memberCount != 2)
            throw new IllegalArgumentException("invalid_conversation_members");
        if ("GROUP".equals(kind) && (memberCount < 1 || memberCount > 20))
            throw new IllegalArgumentException("invalid_member_count");
    }

    public static void validateMessageBody(String bodyText) {
        if (bodyText == null || bodyText.trim().isEmpty() || bodyText.length() > 5000)
            throw new IllegalArgumentException("invalid_message_body");
    }

    public static Set<String> parseGroupCreationMemberIds(String value, String ownAiId) {
        String own = validateAiId(ownAiId);
        if (value == null || value.trim().isEmpty()) {
            Set<String> ownerOnly = new LinkedHashSet<>();
            ownerOnly.add(own);
            return ownerOnly;
        }
        return parseMemberIds(value, own);
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
