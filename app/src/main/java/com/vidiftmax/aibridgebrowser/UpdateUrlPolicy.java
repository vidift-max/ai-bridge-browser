package com.vidiftmax.aibridgebrowser;

import java.net.URI;
import java.net.URISyntaxException;

/** Strict URL-origin policy for official GitHub Release assets and their CDN redirects. */
public final class UpdateUrlPolicy {
    private static final String RELEASE_PATH =
            "/vidift-max/ai-bridge-browser/releases/download/";
    private static final String[] REDIRECT_HOSTS = {
            "github.com", "api.github.com", "objects.githubusercontent.com",
            "release-assets.githubusercontent.com"
    };

    private UpdateUrlPolicy() {}

    public static boolean isOfficialReleaseAssetUrl(String value) {
        URI uri = parse(value);
        return uri != null && isHttpsDefaultPort(uri)
                && "github.com".equalsIgnoreCase(uri.getHost())
                && uri.getRawUserInfo() == null
                && uri.getRawPath() != null
                && uri.getRawPath().startsWith(RELEASE_PATH)
                && uri.getRawPath().length() > RELEASE_PATH.length()
                && uri.getRawQuery() == null && uri.getRawFragment() == null;
    }

    public static boolean isOfficialReleaseAssetUrl(String value, String tagName, String assetName) {
        if (tagName == null || !tagName.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
                || assetName == null || !(assetName.equals("app-release.apk")
                || assetName.equals("ai-bridge-update.json"))) return false;
        URI uri = parse(value);
        String expectedPath = RELEASE_PATH + tagName + "/" + assetName;
        return uri != null && isHttpsDefaultPort(uri)
                && "github.com".equalsIgnoreCase(uri.getHost())
                && uri.getRawUserInfo() == null
                && expectedPath.equals(uri.getRawPath())
                && uri.getRawQuery() == null && uri.getRawFragment() == null;
    }

    public static boolean isAllowedRedirectUrl(String value) {
        URI uri = parse(value);
        if (uri == null || !isHttpsDefaultPort(uri) || uri.getRawUserInfo() != null
                || uri.getHost() == null) return false;
        for (String host : REDIRECT_HOSTS) {
            if (host.equalsIgnoreCase(uri.getHost())) return true;
        }
        return false;
    }

    private static boolean isHttpsDefaultPort(URI uri) {
        return "https".equalsIgnoreCase(uri.getScheme())
                && (uri.getPort() == -1 || uri.getPort() == 443);
    }

    private static URI parse(String value) {
        if (value == null || value.trim().isEmpty()) return null;
        try {
            URI uri = new URI(value);
            if (!uri.isAbsolute() || uri.isOpaque()) return null;
            return uri;
        } catch (URISyntaxException ignored) {
            return null;
        }
    }
}
