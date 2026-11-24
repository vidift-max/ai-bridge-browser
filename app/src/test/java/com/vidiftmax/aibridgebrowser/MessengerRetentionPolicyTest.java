package com.vidiftmax.aibridgebrowser;

import org.junit.Test;

import static org.junit.Assert.*;

public final class MessengerRetentionPolicyTest {
    @Test public void normalGroupExpiresAfterOneHour() {
        long created = 1_000_000L;
        assertEquals(created + MessengerRetentionPolicy.ONE_HOUR_MS,
                MessengerRetentionPolicy.expiresAt(created, "NORMAL", "GROUP"));
        assertFalse(MessengerRetentionPolicy.isExpired(created, "NORMAL", "GROUP",
                created + MessengerRetentionPolicy.ONE_HOUR_MS - 1));
        assertTrue(MessengerRetentionPolicy.isExpired(created, "NORMAL", "GROUP",
                created + MessengerRetentionPolicy.ONE_HOUR_MS));
    }

    @Test public void missionStaysForTwentyFourHoursInCollectiveRoom() {
        long created = 2_000_000L;
        assertEquals(created + MessengerRetentionPolicy.ONE_DAY_MS,
                MessengerRetentionPolicy.expiresAt(created, "MISSION", "GROUP"));
    }

    @Test public void privateTextStaysForTwentyFourHours() {
        long created = 3_000_000L;
        assertEquals(created + MessengerRetentionPolicy.ONE_DAY_MS,
                MessengerRetentionPolicy.expiresAt(created, "NORMAL", "PRIVATE"));
    }

    @Test public void privateMissionAlsoStaysForTwentyFourHours() {
        long created = 4_000_000L;
        assertEquals(created + MessengerRetentionPolicy.ONE_DAY_MS,
                MessengerRetentionPolicy.expiresAt(created, "MISSION", "PRIVATE"));
    }

    @Test public void unknownKindsFailSafeToNormalGroup() {
        assertEquals(MessengerRetentionPolicy.ONE_HOUR_MS,
                MessengerRetentionPolicy.retentionMs("UNKNOWN", "UNKNOWN"));
    }

    @Test public void audioFollowsMessageRetentionByPolicy() {
        assertEquals(MessengerRetentionPolicy.ONE_DAY_MS,
                MessengerRetentionPolicy.retentionMs("MISSION", "GROUP"));
        assertEquals(MessengerRetentionPolicy.ONE_DAY_MS,
                MessengerRetentionPolicy.retentionMs("NORMAL", "PRIVATE"));
    }
}
