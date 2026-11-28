package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class BrowserNavigationPolicyTest {
    private static final String HOME = "https://chatgpt.com/";

    @Test public void allowsHttpsHostAndPath() {
        assertTrue(BrowserNavigationPolicy.isAllowedWebUrl("https://chatgpt.com/"));
        assertTrue(BrowserNavigationPolicy.isAllowedWebUrl("https://example.com/path?q=1#section"));
    }

    @Test public void rejectsHttpAndNonWebSchemes() {
        assertFalse(BrowserNavigationPolicy.isAllowedWebUrl("http://example.com"));
        assertFalse(BrowserNavigationPolicy.isAllowedWebUrl("file:///etc/passwd"));
        assertFalse(BrowserNavigationPolicy.isAllowedWebUrl("javascript:alert(1)"));
        assertFalse(BrowserNavigationPolicy.isAllowedWebUrl("data:text/html,hello"));
        assertFalse(BrowserNavigationPolicy.isAllowedWebUrl("ftp://example.com/file"));
    }

    @Test public void rejectsCredentialsMissingHostsAndInvalidPorts() {
        assertFalse(BrowserNavigationPolicy.isAllowedWebUrl("https://user:pass@example.com"));
        assertFalse(BrowserNavigationPolicy.isAllowedWebUrl("https:///missing-host"));
        assertFalse(BrowserNavigationPolicy.isAllowedWebUrl("https://example.com:99999"));
        assertFalse(BrowserNavigationPolicy.isAllowedWebUrl("https://example.com:abc"));
    }

    @Test public void rejectsRelativeMalformedAndWhitespaceUrls() {
        assertFalse(BrowserNavigationPolicy.isAllowedWebUrl("//example.com/path"));
        assertFalse(BrowserNavigationPolicy.isAllowedWebUrl("https://exa mple.com"));
        assertFalse(BrowserNavigationPolicy.isAllowedWebUrl(" https://example.com"));
        assertFalse(BrowserNavigationPolicy.isAllowedWebUrl(null));
    }

    @Test public void addsHttpsToBareHostsAndUsesSafeFallback() {
        assertEquals("https://example.com/path",
                BrowserNavigationPolicy.normalizeUrl("example.com/path", HOME));
        assertEquals(HOME,
                BrowserNavigationPolicy.normalizeUrl("http://example.com", HOME));
        assertEquals(HOME,
                BrowserNavigationPolicy.normalizeUrl("javascript:alert(1)", HOME));
        assertEquals(HOME,
                BrowserNavigationPolicy.normalizeUrl("", HOME));
    }
}
