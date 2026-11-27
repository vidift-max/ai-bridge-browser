package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.*;

import org.junit.Test;

public class InviteLinkParserTest {
    private static final String TOKEN = "ABCDEFGHIJKLMNOPQRST";

    @Test public void parsesCustomScheme() {
        InviteLinkParser.Invite invite =
                InviteLinkParser.parse("aibridge://invite/room_01/" + TOKEN);
        assertNotNull(invite);
        assertEquals("room_01", invite.conversationId);
        assertEquals(TOKEN, invite.token);
    }

    @Test public void parsesWebAppInvite() {
        InviteLinkParser.Invite invite =
                InviteLinkParser.parse("https://example.web.app/i/room-01/" + TOKEN);
        assertNotNull(invite);
        assertEquals("room-01", invite.conversationId);
    }

    @Test public void acceptsNestedWebAppSubdomain() {
        assertNotNull(InviteLinkParser.parse(
                "https://preview-123.example.web.app/i/room/" + TOKEN));
    }

    @Test public void rejectsQueryFragmentAndUserInfo() {
        assertNull(InviteLinkParser.parse("aibridge://invite/room/" + TOKEN + "?x=1"));
        assertNull(InviteLinkParser.parse("https://example.web.app/i/room/" + TOKEN + "#x"));
        assertNull(InviteLinkParser.parse("https://user@example.web.app/i/room/" + TOKEN));
    }

    @Test public void rejectsInvalidTokenAndConversation() {
        assertNull(InviteLinkParser.parse("aibridge://invite/room/too-short"));
        assertNull(InviteLinkParser.parse("aibridge://invite/bad.id/" + TOKEN));
        assertNull(InviteLinkParser.parse("aibridge://invite//" + TOKEN));
    }

    @Test public void rejectsPortAndExternalWhitespace() {
        assertNull(InviteLinkParser.parse("https://example.web.app:443/i/room/" + TOKEN));
        assertNull(InviteLinkParser.parse(" https://example.web.app/i/room/" + TOKEN));
        assertNull(InviteLinkParser.parse("https://example.web.app/i/room/" + TOKEN + " "));
    }

    @Test public void rejectsWrongSchemeAndHost() {
        assertNull(InviteLinkParser.parse("http://example.web.app/i/room/" + TOKEN));
        assertNull(InviteLinkParser.parse("https://example.com/i/room/" + TOKEN));
        assertNull(InviteLinkParser.parse("aibridge://other/room/" + TOKEN));
    }

    @Test public void rejectsNullEmptyAndExtraPathSegments() {
        assertNull(InviteLinkParser.parse(null));
        assertNull(InviteLinkParser.parse(""));
        assertNull(InviteLinkParser.parse("aibridge://invite/room/" + TOKEN + "/extra"));
        assertNull(InviteLinkParser.parse("https://example.web.app/i/room/" + TOKEN + "/extra"));
    }
}
