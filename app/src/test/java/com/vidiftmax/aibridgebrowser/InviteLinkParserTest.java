package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import static org.junit.Assert.*;

public class InviteLinkParserTest {
    private static final String TOKEN = "Abcdefghijklmnopqrstuvwxyz_123456";

    @Test public void parses_app_scheme_invite() {
        InviteLinkParser.Invite invite = InviteLinkParser.parse("aibridge://invite/room_01/" + TOKEN);
        assertNotNull(invite);
        assertEquals("room_01", invite.conversationId);
        assertEquals(TOKEN, invite.token);
    }

    @Test public void parses_https_firebase_invite() {
        InviteLinkParser.Invite invite = InviteLinkParser.parse("https://project.web.app/i/room-02/" + TOKEN);
        assertNotNull(invite);
        assertEquals("room-02", invite.conversationId);
        assertEquals(TOKEN, invite.token);
    }

    @Test public void accepts_case_insensitive_scheme_and_host() {
        assertNotNull(InviteLinkParser.parse("AIBRIDGE://INVITE/room/" + TOKEN));
        assertNotNull(InviteLinkParser.parse("HTTPS://PROJECT.WEB.APP/i/room/" + TOKEN));
    }

    @Test public void rejects_null_blank_and_whitespace_wrapped_links() {
        assertNull(InviteLinkParser.parse(null));
        assertNull(InviteLinkParser.parse(""));
        assertNull(InviteLinkParser.parse("  aibridge://invite/room/" + TOKEN));
    }

    @Test public void rejects_untrusted_scheme_and_host() {
        assertNull(InviteLinkParser.parse("http://project.web.app/i/room/" + TOKEN));
        assertNull(InviteLinkParser.parse("https://project.example.com/i/room/" + TOKEN));
        assertNull(InviteLinkParser.parse("aibridge://other/room/" + TOKEN));
    }

    @Test public void rejects_host_suffix_spoofing_and_userinfo() {
        assertNull(InviteLinkParser.parse("https://project.web.app.attacker.test/i/room/" + TOKEN));
        assertNull(InviteLinkParser.parse("https://project.web.app@attacker.test/i/room/" + TOKEN));
    }

    @Test public void rejects_ports_queries_and_fragments() {
        assertNull(InviteLinkParser.parse("https://project.web.app:443/i/room/" + TOKEN));
        assertNull(InviteLinkParser.parse("https://project.web.app/i/room/" + TOKEN + "?next=x"));
        assertNull(InviteLinkParser.parse("https://project.web.app/i/room/" + TOKEN + "#other"));
    }

    @Test public void rejects_wrong_path_shapes_and_encoded_segments() {
        assertNull(InviteLinkParser.parse("https://project.web.app/room/" + TOKEN));
        assertNull(InviteLinkParser.parse("https://project.web.app/i/room/" + TOKEN + "/extra"));
        assertNull(InviteLinkParser.parse("https://project.web.app/i/room%2Fother/" + TOKEN));
    }

    @Test public void rejects_invalid_conversation_ids() {
        assertNull(InviteLinkParser.parse("aibridge://invite/" + "x".repeat(129) + "/" + TOKEN));
        assertNull(InviteLinkParser.parse("aibridge://invite/room%20name/" + TOKEN));
    }

    @Test public void enforces_token_length_and_charset() {
        assertNull(InviteLinkParser.parse("aibridge://invite/room/short"));
        assertNull(InviteLinkParser.parse("aibridge://invite/room/" + "x".repeat(65)));
        assertNull(InviteLinkParser.parse("aibridge://invite/room/" + "x".repeat(25) + "!"));
    }

    @Test public void accepts_token_length_boundaries() {
        assertNotNull(InviteLinkParser.parse("aibridge://invite/room/" + "x".repeat(20)));
        assertNotNull(InviteLinkParser.parse("aibridge://invite/room/" + "x".repeat(64)));
    }
}
