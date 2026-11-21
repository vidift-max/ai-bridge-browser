package com.vidiftmax.aibridgebrowser;

import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;

public final class MessengerTransportRecordTest {
    @Test
    public void createsLocalOutboxRecordWithStableIds() {
        MessengerTransportRecord record = new MessengerTransportRecord(
                "message-1", "LOCAL-room", MessengerTransportRecord.DIRECTION_OUTBOX,
                "CONTACT-1", 1700000000000L);

        assertEquals(MessengerTransportRecord.DIRECTION_OUTBOX, record.getDirection());
        assertEquals(MessengerTransportRecord.STATUS_LOCAL_ONLY, record.getStatus());
        assertEquals("message-1", record.getMessageId());
        assertEquals("LOCAL-room", record.getConversationId());
        assertEquals("CONTACT-1", record.getParticipantLocalId());
        assertNotEquals(record.getMessageId(), record.getRecordId());
    }

    @Test
    public void createsLocalInboxRecordWithoutClaimingDelivery() {
        MessengerTransportRecord record = new MessengerTransportRecord(
                "message-2", "LOCAL-room", MessengerTransportRecord.DIRECTION_INBOX,
                "CONTACT-2", 1700000000000L);

        assertEquals(MessengerTransportRecord.DIRECTION_INBOX, record.getDirection());
        assertEquals(MessengerTransportRecord.STATUS_LOCAL_ONLY, record.getStatus());
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsRemoteLookingDirection() {
        new MessengerTransportRecord(
                "message-3", "LOCAL-room", "DELIVERED", "CONTACT-3", 1700000000000L);
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsMissingParticipant() {
        new MessengerTransportRecord(
                "message-4", "LOCAL-room", MessengerTransportRecord.DIRECTION_OUTBOX,
                "", 1700000000000L);
    }
}
