package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import static org.junit.Assert.*;

public class InviteBrowserRouteTest {
    private static final String TOKEN = "Abcdefghijklmnopqrstuvwxyz_123456";
    @Test public void accepts_web_ui_invite_shape() {
        assertEquals("https://project.web.app/invite#invite_123." + TOKEN,
                InviteBrowserRoute.toWebUrl("https://project.web.app/invite#invite_123." + TOKEN));
    }
    @Test public void normalizes_scheme_and_host_case() {
        assertEquals("https://project.web.app/invite#id." + TOKEN,
                InviteBrowserRoute.toWebUrl("HTTPS://PROJECT.WEB.APP/invite#id." + TOKEN));
    }
    @Test public void rejects_native_route_shape_and_untrusted_hosts() {
        assertNull(InviteBrowserRoute.toWebUrl("https://project.web.app/i/room/" + TOKEN));
        assertNull(InviteBrowserRoute.toWebUrl("https://project.example.com/invite#id." + TOKEN));
        assertNull(InviteBrowserRoute.toWebUrl("https://project.web.app.attacker.test/invite#id." + TOKEN));
    }
    @Test public void rejects_credentials_ports_query_and_missing_fragment() {
        assertNull(InviteBrowserRoute.toWebUrl("https://user@project.web.app/invite#id." + TOKEN));
        assertNull(InviteBrowserRoute.toWebUrl("https://project.web.app:443/invite#id." + TOKEN));
        assertNull(InviteBrowserRoute.toWebUrl("https://project.web.app/invite?token=x#id." + TOKEN));
        assertNull(InviteBrowserRoute.toWebUrl("https://project.web.app/invite"));
    }
    @Test public void rejects_malformed_fragment_and_paths() {
        assertNull(InviteBrowserRoute.toWebUrl("https://project.web.app/rooms#id." + TOKEN));
        assertNull(InviteBrowserRoute.toWebUrl("https://project.web.app/invite#id"));
        assertNull(InviteBrowserRoute.toWebUrl("https://project.web.app/invite#id.short"));
        assertNull(InviteBrowserRoute.toWebUrl("https://project.web.app/invite#id." + TOKEN + ".extra"));
        assertNull(InviteBrowserRoute.toWebUrl("https://project.web.app/invite#id." + TOKEN + "%2F"));
    }
    @Test public void rejects_null_empty_and_whitespace() {
        assertNull(InviteBrowserRoute.toWebUrl(null));
        assertNull(InviteBrowserRoute.toWebUrl(""));
        assertNull(InviteBrowserRoute.toWebUrl(" https://project.web.app/invite#id." + TOKEN));
    }
}
