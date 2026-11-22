package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import static org.junit.Assert.*;

public class AiPhoneRegistryConfigTest {
    @Test public void acceptsHttpsAndRemovesTrailingSlash() {
        assertEquals("https://registry.example.com/api",
                AiPhoneRegistryConfig.normalizeBaseUrl(" https://registry.example.com/api/// "));
    }

    @Test public void rejectsHttpAndCredentialBearingUrls() {
        assertThrows(IllegalArgumentException.class,
                () -> AiPhoneRegistryConfig.normalizeBaseUrl("http://registry.example.com"));
        assertThrows(IllegalArgumentException.class,
                () -> AiPhoneRegistryConfig.normalizeBaseUrl("https://user:pass@example.com"));
        assertThrows(IllegalArgumentException.class,
                () -> AiPhoneRegistryConfig.normalizeBaseUrl("https://example.com?token=secret"));
    }

    @Test public void validatesAiId() {
        assertEquals("AI-GPT6", AiPhoneRegistryConfig.validateAiId("AI-GPT6"));
        assertThrows(IllegalArgumentException.class,
                () -> AiPhoneRegistryConfig.validateAiId("gpt6"));
        assertThrows(IllegalArgumentException.class,
                () -> AiPhoneRegistryConfig.validateAiId("AI-GPT6/../admin"));
    }
}
