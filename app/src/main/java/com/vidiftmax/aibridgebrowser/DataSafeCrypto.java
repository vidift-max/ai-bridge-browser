package com.vidiftmax.aibridgebrowser;

import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.security.GeneralSecurityException;
import java.security.SecureRandom;
import java.util.Arrays;
import javax.crypto.AEADBadTagException;
import javax.crypto.Cipher;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.SecretKeySpec;

/** Password-based authenticated encryption envelope for DATA SAFE payloads. */
public final class DataSafeCrypto {
    private static final byte[] MAGIC = new byte[] {'A','I','P','S','A','F','E','1'};
    private static final int VERSION = 1;
    private static final int SALT_BYTES = 16;
    private static final int NONCE_BYTES = 12;
    private static final int TAG_BITS = 128;
    private static final int HEADER_BYTES = MAGIC.length + 1 + 4 + SALT_BYTES + NONCE_BYTES;
    private static final int MIN_ITERATIONS = 310_000;
    private static final int MAX_ITERATIONS = 1_000_000;
    private static final int KEY_BITS = 256;

    private DataSafeCrypto() {}

    public static byte[] encrypt(byte[] plaintext, char[] password) throws GeneralSecurityException {
        return encrypt(plaintext, password, new SecureRandom());
    }

    static byte[] encrypt(byte[] plaintext, char[] password, SecureRandom random)
            throws GeneralSecurityException {
        if (plaintext == null) throw new IllegalArgumentException("plaintext_required");
        validatePassword(password);
        if (plaintext.length > DataSafeLimits.MAX_ARCHIVE_BYTES)
            throw new IllegalArgumentException("payload_too_large");
        if (random == null) throw new IllegalArgumentException("random_required");

        byte[] salt = new byte[SALT_BYTES];
        byte[] nonce = new byte[NONCE_BYTES];
        random.nextBytes(salt);
        random.nextBytes(nonce);
        byte[] header = ByteBuffer.allocate(HEADER_BYTES)
                .put(MAGIC).put((byte) VERSION).putInt(MIN_ITERATIONS)
                .put(salt).put(nonce).array();
        byte[] key = deriveKey(password, salt, MIN_ITERATIONS);
        try {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(key, "AES"),
                    new GCMParameterSpec(TAG_BITS, nonce));
            cipher.updateAAD(header);
            byte[] encrypted = cipher.doFinal(plaintext);
            ByteArrayOutputStream out = new ByteArrayOutputStream(header.length + encrypted.length);
            out.write(header, 0, header.length);
            out.write(encrypted, 0, encrypted.length);
            Arrays.fill(encrypted, (byte) 0);
            return out.toByteArray();
        } finally {
            Arrays.fill(key, (byte) 0);
            Arrays.fill(salt, (byte) 0);
            Arrays.fill(nonce, (byte) 0);
        }
    }

    public static byte[] decrypt(byte[] envelope, char[] password) throws GeneralSecurityException {
        if (envelope == null) throw new IllegalArgumentException("envelope_required");
        validatePassword(password);
        if (envelope.length < HEADER_BYTES + 16)
            throw new GeneralSecurityException("envelope_truncated");
        if (envelope.length > DataSafeLimits.MAX_ARCHIVE_BYTES + HEADER_BYTES + 16)
            throw new GeneralSecurityException("envelope_too_large");

        ByteBuffer input = ByteBuffer.wrap(envelope);
        byte[] magic = new byte[MAGIC.length];
        input.get(magic);
        if (!Arrays.equals(MAGIC, magic)) throw new GeneralSecurityException("format_invalid");
        int version = input.get() & 0xff;
        if (version != VERSION) throw new GeneralSecurityException("version_unsupported");
        int iterations = input.getInt();
        if (iterations < MIN_ITERATIONS || iterations > MAX_ITERATIONS)
            throw new GeneralSecurityException("kdf_parameters_invalid");
        byte[] salt = new byte[SALT_BYTES];
        byte[] nonce = new byte[NONCE_BYTES];
        input.get(salt);
        input.get(nonce);
        byte[] header = Arrays.copyOf(envelope, HEADER_BYTES);
        byte[] ciphertext = Arrays.copyOfRange(envelope, HEADER_BYTES, envelope.length);
        byte[] key = deriveKey(password, salt, iterations);
        try {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE, new SecretKeySpec(key, "AES"),
                    new GCMParameterSpec(TAG_BITS, nonce));
            cipher.updateAAD(header);
            return cipher.doFinal(ciphertext);
        } catch (AEADBadTagException e) {
            throw new GeneralSecurityException("authentication_failed", e);
        } finally {
            Arrays.fill(key, (byte) 0);
            Arrays.fill(salt, (byte) 0);
            Arrays.fill(nonce, (byte) 0);
            Arrays.fill(ciphertext, (byte) 0);
        }
    }

    private static byte[] deriveKey(char[] password, byte[] salt, int iterations)
            throws GeneralSecurityException {
        PBEKeySpec spec = new PBEKeySpec(password, salt, iterations, KEY_BITS);
        try {
            return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
                    .generateSecret(spec).getEncoded();
        } finally {
            spec.clearPassword();
        }
    }

    private static void validatePassword(char[] password) {
        if (password == null || password.length < 12 || password.length > 1024)
            throw new IllegalArgumentException("password_length_invalid");
    }
}
