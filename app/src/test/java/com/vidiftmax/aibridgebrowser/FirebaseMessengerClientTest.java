package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import static org.junit.Assert.*;

public class FirebaseMessengerClientTest {
    @Test public void acceptsFirebaseDatabaseHosts() {
        assertTrue(FirebaseMessengerClient.isFirebaseDatabaseUrl("https://demo.firebaseio.com"));
        assertTrue(FirebaseMessengerClient.isFirebaseDatabaseUrl("https://demo-default-rtdb.firebaseio.com"));
        assertTrue(FirebaseMessengerClient.isFirebaseDatabaseUrl("https://demo-default-rtdb.europe-west1.firebasedatabase.app"));
    }

    @Test public void rejectsNonFirebaseHosts() {
        assertFalse(FirebaseMessengerClient.isFirebaseDatabaseUrl("https://example.com"));
        assertFalse(FirebaseMessengerClient.isFirebaseDatabaseUrl("http://demo.firebaseio.com"));
        assertFalse(FirebaseMessengerClient.isFirebaseDatabaseUrl("https://demo.firebaseio.com?x=1"));
        assertFalse(FirebaseMessengerClient.isFirebaseDatabaseUrl("https://demo.firebaseio.com/#fragment"));
    }

    @Test public void normalizesTrailingSlash() {
        assertEquals("https://demo.firebaseio.com",
                FirebaseMessengerClient.normalizeDatabaseUrl("https://demo.firebaseio.com///"));
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsQueryInDatabaseUrl() {
        FirebaseMessengerClient.normalizeDatabaseUrl("https://demo.firebaseio.com?x=1");
    }
}
