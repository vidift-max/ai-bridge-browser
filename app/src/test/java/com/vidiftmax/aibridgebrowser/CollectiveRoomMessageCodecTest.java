package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import static org.junit.Assert.*;

public final class CollectiveRoomMessageCodecTest {
    @Test public void roundTripsOiMessageForLocalRoomDisplay() {
        String line = CollectiveRoomMessageCodec.encode(
                1_800_000_000_000L, "NORMAL", "GPT-6", "🤖", "OI");
        CollectiveRoomMessageCodec.Message decoded = CollectiveRoomMessageCodec.decode(line);
        assertNotNull(decoded);
        assertEquals("OI", decoded.body);
        assertEquals("GPT-6", decoded.sender);
        assertEquals("🤖", decoded.avatar);
        assertEquals(MessengerRetentionPolicy.MESSAGE_NORMAL, decoded.kind);
    }

    @Test public void safelyKeepsMessageOnOneStorageLine() {
        String line = CollectiveRoomMessageCodec.encode(
                1_800_000_000_000L, "MISSION", "AI|NAME", "🤖", "OI|\nTUDO BEM?");
        assertFalse(line.contains("\n"));
        assertEquals("AI¦NAME", CollectiveRoomMessageCodec.decode(line).sender);
        assertEquals("OI¦ TUDO BEM?", CollectiveRoomMessageCodec.decode(line).body);
    }

    @Test public void rejectsMalformedOrInvalidTimestampRows() {
        assertNull(CollectiveRoomMessageCodec.decode(null));
        assertNull(CollectiveRoomMessageCodec.decode("bad|NORMAL|AI|🤖|OI"));
        assertNull(CollectiveRoomMessageCodec.decode("0|NORMAL|AI|🤖|OI"));
        assertNull(CollectiveRoomMessageCodec.decode("1|NORMAL|AI"));
    }

    @Test public void unknownMessageKindNormalizesToNormal() {
        CollectiveRoomMessageCodec.Message decoded = CollectiveRoomMessageCodec.decode(
                "1800000000000|UNKNOWN|AI|🤖|OI");
        assertNotNull(decoded);
        assertEquals(MessengerRetentionPolicy.MESSAGE_NORMAL, decoded.kind);
    }
}
