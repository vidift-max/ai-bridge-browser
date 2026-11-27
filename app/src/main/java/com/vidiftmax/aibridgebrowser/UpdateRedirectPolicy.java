package com.vidiftmax.aibridgebrowser;

import java.net.URI;
import java.net.URISyntaxException;

/** Validates each HTTP redirect hop before the updater follows it. */
public final class UpdateRedirectPolicy {
    private UpdateRedirectPolicy() {}

    public static boolean isRedirectStatus(int statusCode) {
        return statusCode == 301 || statusCode == 302 || statusCode == 303
                || statusCode == 307 || statusCode == 308;
    }

    public static String resolveRedirectUrl(String currentUrl, String location,
            int redirectsFollowed, int maximumRedirects) {
        if (currentUrl == null || location == null || location.trim().isEmpty()
                || redirectsFollowed < 0 || maximumRedirects < 0
                || redirectsFollowed >= maximumRedirects) return null;
        try {
            URI current = new URI(currentUrl);
            URI next = current.resolve(new URI(location.trim()));
            String resolved = next.toASCIIString();
            return UpdateUrlPolicy.isAllowedRedirectUrl(resolved) ? resolved : null;
        } catch (URISyntaxException | IllegalArgumentException ignored) {
            return null;
        }
    }
}
