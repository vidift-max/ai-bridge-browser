package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;
import org.junit.Test;

public class AiPhoneRegistryConfigTest {
    @Test public void acceptsHttpsOriginAndNormalizesTrailingSlash() {
        assertEquals("https://registry.example", AiPhoneRegistryConfig.normalizeBaseUrl(" https://Registry.Example/ "));
        assertEquals("https://registry.example:8443", AiPhoneRegistryConfig.normalizeBaseUrl("https://registry.example:8443"));
    }

    @Test public void rejectsHttpAndUrlWithPathOrCredentials() {
        assertThrows(IllegalArgumentException.class, () -> AiPhoneRegistryConfig.normalizeBaseUrl("http://registry.example"));
        assertThrows(IllegalArgumentException.class, () -> AiPhoneRegistryConfig.normalizeBaseUrl("https://registry.example/api"));
        assertThrows(IllegalArgumentException.class, () -> AiPhoneRegistryConfig.normalizeBaseUrl("https://user:pass@registry.example"));
        assertThrows(IllegalArgumentException.class, () -> AiPhoneRegistryConfig.normalizeBaseUrl("https://registry.example?token=x"));
    }

    @Test public void rejectsEmptyOrigin() {
        assertThrows(IllegalArgumentException.class, () -> AiPhoneRegistryConfig.normalizeBaseUrl(" "));
    }
}
