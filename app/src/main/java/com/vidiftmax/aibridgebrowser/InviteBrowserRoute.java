package com.vidiftmax.aibridgebrowser;

import java.net.URI;
import java.util.Locale;

/** Parses the actual web invite URL shape: https://host.web.app/invite#inviteId.token */
final class InviteBrowserRoute {
    private InviteBrowserRoute() { }

    static String toWebUrl(String value) {
        if (value == null || value.isEmpty() || !value.equals(value.trim())) return null;
        try {
            URI uri = new URI(value);
            String scheme = uri.getScheme();
            String host = uri.getHost();
            String path = uri.getRawPath();
            String fragment = uri.getRawFragment();
            if (scheme == null || !"https".equalsIgnoreCase(scheme) || host == null
                    || uri.isOpaque() || uri.getRawUserInfo() != null || uri.getPort() != -1
                    || uri.getRawQuery() != null || path == null || !"/invite".equals(path)
                    || fragment == null || fragment.indexOf('%') >= 0) return null;
            String normalizedHost = host.toLowerCase(Locale.ROOT);
            if (!normalizedHost.matches("[a-z0-9-]+(?:\\.[a-z0-9-]+)*\\.web\\.app")) return null;
            String[] parts = fragment.split("\\.", -1);
            if (parts.length != 2 || !parts[0].matches("[A-Za-z0-9_-]{1,128}")
                    || !parts[1].matches("[A-Za-z0-9_-]{20,256}")) return null;
            return "https://" + normalizedHost + "/invite#" + parts[0] + "." + parts[1];
        } catch (Exception ignored) {
            return null;
        }
    }
}
