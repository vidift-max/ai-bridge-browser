package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class UpdateRedirectPolicyTest {
    private static final String RELEASE =
            "https://github.com/vidift-max/ai-bridge-browser/releases/download/v1.0/app-release.apk";

    @Test public void recognizesOnlySupportedRedirectStatuses() {
        assertTrue(UpdateRedirectPolicy.isRedirectStatus(301));
        assertTrue(UpdateRedirectPolicy.isRedirectStatus(302));
        assertTrue(UpdateRedirectPolicy.isRedirectStatus(303));
        assertTrue(UpdateRedirectPolicy.isRedirectStatus(307));
        assertTrue(UpdateRedirectPolicy.isRedirectStatus(308));
        assertFalse(UpdateRedirectPolicy.isRedirectStatus(300));
        assertFalse(UpdateRedirectPolicy.isRedirectStatus(200));
        assertFalse(UpdateRedirectPolicy.isRedirectStatus(404));
    }

    @Test public void resolvesRelativeRedirectToAllowedGithubCdn() {
        assertEquals("https://objects.githubusercontent.com/file",
                UpdateRedirectPolicy.resolveRedirectUrl(RELEASE,
                        "https://objects.githubusercontent.com/file", 0, 5));
        assertEquals("https://github.com/next",
                UpdateRedirectPolicy.resolveRedirectUrl(RELEASE, "/next", 0, 5));
    }

    @Test public void rejectsUntrustedRedirectTargets() {
        assertNull(UpdateRedirectPolicy.resolveRedirectUrl(RELEASE,
                "https://evil.example/file", 0, 5));
        assertNull(UpdateRedirectPolicy.resolveRedirectUrl(RELEASE,
                "http://github.com/file", 0, 5));
        assertNull(UpdateRedirectPolicy.resolveRedirectUrl(RELEASE,
                "//evil.example/file", 0, 5));
        assertNull(UpdateRedirectPolicy.resolveRedirectUrl(RELEASE,
                "https://user@github.com/file", 0, 5));
        assertNull(UpdateRedirectPolicy.resolveRedirectUrl(RELEASE,
                "https://github.com:8443/file", 0, 5));
    }

    @Test public void rejectsMissingMalformedAndExcessiveRedirects() {
        assertNull(UpdateRedirectPolicy.resolveRedirectUrl(RELEASE, null, 0, 5));
        assertNull(UpdateRedirectPolicy.resolveRedirectUrl(RELEASE, " ", 0, 5));
        assertNull(UpdateRedirectPolicy.resolveRedirectUrl(RELEASE, "http://[", 0, 5));
        assertNull(UpdateRedirectPolicy.resolveRedirectUrl(RELEASE, "/next", 5, 5));
        assertNull(UpdateRedirectPolicy.resolveRedirectUrl(RELEASE, "/next", 0, 0));
        assertNull(UpdateRedirectPolicy.resolveRedirectUrl(RELEASE, "/next", -1, 5));
    }
}
