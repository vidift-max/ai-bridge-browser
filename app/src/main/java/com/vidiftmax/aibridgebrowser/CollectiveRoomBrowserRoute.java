package com.vidiftmax.aibridgebrowser;

import java.net.URI;
import java.util.Locale;

/** Validates the HTTPS web route used to open the collective room in the active browser tab. */
final class CollectiveRoomBrowserRoute {
    private CollectiveRoomBrowserRoute() { }

    static String validate(String value) {
        if (value == null || !value.equals(value.trim()) || value.isEmpty()) return null;
        try {
            URI uri = new URI(value);
            String scheme = uri.getScheme();
            String host = uri.getHost();
            String path = uri.getRawPath();
            if (scheme == null || !"https".equalsIgnoreCase(scheme) || host == null
                    || uri.getRawUserInfo() != null || uri.getPort() != -1
                    || uri.getRawQuery() != null || uri.getRawFragment() != null
                    || uri.isOpaque()) return null;
            if (path == null || !(path.equals("/rooms") || path.equals("/rooms.html"))) return null;
            if (host.indexOf('%') >= 0 || host.contains("..")) return null;
            return "https://" + host.toLowerCase(Locale.ROOT) + path;
        } catch (Exception ignored) {
            return null;
        }
    }
}
