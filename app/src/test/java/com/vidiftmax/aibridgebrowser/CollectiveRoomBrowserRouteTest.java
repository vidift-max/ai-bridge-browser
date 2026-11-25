package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import static org.junit.Assert.*;

public class CollectiveRoomBrowserRouteTest {
    @Test public void accepts_https_room_routes() {
        assertEquals("https://bridge.example/rooms.html",
                CollectiveRoomBrowserRoute.validate("https://bridge.example/rooms.html"));
        assertEquals("https://bridge.example/rooms",
                CollectiveRoomBrowserRoute.validate("https://bridge.example/rooms"));
    }

    @Test public void normalizes_host_case() {
        assertEquals("https://bridge.example/rooms.html",
                CollectiveRoomBrowserRoute.validate("https://BRIDGE.EXAMPLE/rooms.html"));
    }

    @Test public void rejects_non_https_and_missing_hosts() {
        assertNull(CollectiveRoomBrowserRoute.validate("http://bridge.example/rooms.html"));
        assertNull(CollectiveRoomBrowserRoute.validate("file:///rooms.html"));
        assertNull(CollectiveRoomBrowserRoute.validate("https:///rooms.html"));
    }

    @Test public void rejects_credentials_ports_query_and_fragment() {
        assertNull(CollectiveRoomBrowserRoute.validate("https://user@bridge.example/rooms.html"));
        assertNull(CollectiveRoomBrowserRoute.validate("https://bridge.example:443/rooms.html"));
        assertNull(CollectiveRoomBrowserRoute.validate("https://bridge.example/rooms.html?token=x"));
        assertNull(CollectiveRoomBrowserRoute.validate("https://bridge.example/rooms.html#invite"));
    }

    @Test public void rejects_wrong_paths_and_encoded_paths() {
        assertNull(CollectiveRoomBrowserRoute.validate("https://bridge.example/"));
        assertNull(CollectiveRoomBrowserRoute.validate("https://bridge.example/invite"));
        assertNull(CollectiveRoomBrowserRoute.validate("https://bridge.example/%72ooms.html"));
        assertNull(CollectiveRoomBrowserRoute.validate("https://bridge.example/rooms.html/extra"));
    }

    @Test public void rejects_whitespace_and_null() {
        assertNull(CollectiveRoomBrowserRoute.validate(null));
        assertNull(CollectiveRoomBrowserRoute.validate(""));
        assertNull(CollectiveRoomBrowserRoute.validate(" https://bridge.example/rooms.html"));
    }
}
