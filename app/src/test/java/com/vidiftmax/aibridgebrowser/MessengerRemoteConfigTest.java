package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import static org.junit.Assert.assertEquals;

public class MessengerRemoteConfigTest {
    @Test public void group_allows_exactly_twenty_members() {
        assertEquals(20, MessengerRemoteConfig.parseMemberIds(
                "AI-02,AI-03,AI-04,AI-05,AI-06,AI-07,AI-08,AI-09,AI-10,AI-11,AI-12,AI-13,AI-14,AI-15,AI-16,AI-17,AI-18,AI-19,AI-20",
                "AI-01").size());
    }

    @Test(expected = IllegalArgumentException.class)
    public void group_rejects_more_than_twenty_members() {
        MessengerRemoteConfig.parseMemberIds(
                "AI-02,AI-03,AI-04,AI-05,AI-06,AI-07,AI-08,AI-09,AI-10,AI-11,AI-12,AI-13,AI-14,AI-15,AI-16,AI-17,AI-18,AI-19,AI-20,AI-21",
                "AI-01");
    }

    @Test(expected = IllegalArgumentException.class)
    public void private_conversation_rejects_more_than_two_members() {
        MessengerRemoteConfig.validateConversationMemberCount("PRIVATE", 3);
    }
    @Test public void accepts_only_https_firebase_hosting_domains_for_invites() {
        org.junit.Assert.assertEquals("https://my-project.web.app",
                MessengerRemoteConfig.normalizeInviteHostingUrl("https://my-project.web.app/"));
    }

    @Test(expected = IllegalArgumentException.class)
    public void invite_host_rejects_non_firebase_domains() {
        MessengerRemoteConfig.normalizeInviteHostingUrl("https://example.com");
    }

    @Test(expected = IllegalArgumentException.class)
    public void invite_host_rejects_http() {
        MessengerRemoteConfig.normalizeInviteHostingUrl("http://my-project.web.app");
    }

    @Test(expected = IllegalArgumentException.class)
    public void invite_host_rejects_paths_and_query_strings() {
        MessengerRemoteConfig.normalizeInviteHostingUrl("https://my-project.web.app/rooms?x=1");
    }

}
