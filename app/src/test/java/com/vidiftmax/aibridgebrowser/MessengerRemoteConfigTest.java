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

    @Test public void group_invite_requires_group_owned_by_current_ai() {
        MessengerRemoteConfig.validateGroupInviteOwner("GROUP", "AI-01", "AI-01");
    }

    @Test(expected = IllegalArgumentException.class)
    public void group_invite_rejects_private_conversation() {
        MessengerRemoteConfig.validateGroupInviteOwner("PRIVATE", "AI-01", "AI-01");
    }

    @Test(expected = IllegalArgumentException.class)
    public void group_invite_rejects_non_owner() {
        MessengerRemoteConfig.validateGroupInviteOwner("GROUP", "AI-01", "AI-02");
    }

    @Test(expected = IllegalArgumentException.class)
    public void private_conversation_rejects_more_than_two_members() {
        MessengerRemoteConfig.validateConversationMemberCount("PRIVATE", 3);
    }
}
