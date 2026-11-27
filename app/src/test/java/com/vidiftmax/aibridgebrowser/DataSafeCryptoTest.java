package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import java.security.GeneralSecurityException;
import static org.junit.Assert.*;

public final class DataSafeCryptoTest {
    private static final char[] PASSWORD = "correct horse battery staple".toCharArray();

    @Test public void encryptDecryptRoundTrip() throws Exception {
        byte[] original = "AI-PHONE DATA SAFE".getBytes("UTF-8");
        byte[] encrypted = DataSafeCrypto.encrypt(original, PASSWORD);
        assertFalse(java.util.Arrays.equals(original, encrypted));
        assertArrayEquals(original, DataSafeCrypto.decrypt(encrypted, PASSWORD));
    }

    @Test public void eachEncryptionUsesDifferentSaltAndNonce() throws Exception {
        byte[] payload = new byte[] {1, 2, 3};
        assertFalse(java.util.Arrays.equals(
                DataSafeCrypto.encrypt(payload, PASSWORD),
                DataSafeCrypto.encrypt(payload, PASSWORD)));
    }

    @Test(expected = GeneralSecurityException.class)
    public void wrongPasswordIsRejected() throws Exception {
        byte[] encrypted = DataSafeCrypto.encrypt(new byte[] {9}, PASSWORD);
        DataSafeCrypto.decrypt(encrypted, "different secure password".toCharArray());
    }

    @Test(expected = GeneralSecurityException.class)
    public void modifiedCiphertextIsRejected() throws Exception {
        byte[] encrypted = DataSafeCrypto.encrypt(new byte[] {4, 5, 6}, PASSWORD);
        encrypted[encrypted.length - 1] ^= 1;
        DataSafeCrypto.decrypt(encrypted, PASSWORD);
    }

    @Test(expected = GeneralSecurityException.class)
    public void truncatedEnvelopeIsRejected() throws Exception {
        DataSafeCrypto.decrypt(new byte[] {1, 2, 3}, PASSWORD);
    }

    @Test(expected = IllegalArgumentException.class)
    public void shortPasswordIsRejected() throws Exception {
        DataSafeCrypto.encrypt(new byte[] {1}, "short".toCharArray());
    }
}
