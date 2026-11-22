package com.vidiftmax.aibridgebrowser;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Encrypts the registry bearer token with a non-exportable Android Keystore AES key. */
public final class AiPhoneSecretStore {
    private static final String PREFS = "ai_phone_registry_connection_v1";
    private static final String KEY_CIPHER = "encrypted_bearer_token";
    private static final String KEY_ALIAS = "ai_phone_registry_token_v1";
    private static final String ANDROID_KEY_STORE = "AndroidKeyStore";
    private AiPhoneSecretStore() {}

    public static void save(Context context, String token) throws Exception {
        if (token == null || token.trim().isEmpty()) throw new IllegalArgumentException("Token obrigatório.");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey());
        byte[] encrypted = cipher.doFinal(token.trim().getBytes("UTF-8"));
        byte[] iv = cipher.getIV();
        byte[] combined = new byte[iv.length + encrypted.length];
        System.arraycopy(iv, 0, combined, 0, iv.length);
        System.arraycopy(encrypted, 0, combined, iv.length, encrypted.length);
        prefs(context).edit().putString(KEY_CIPHER, Base64.encodeToString(combined, Base64.NO_WRAP)).apply();
    }

    public static String load(Context context) throws Exception {
        String encoded = prefs(context).getString(KEY_CIPHER, "");
        if (encoded.isEmpty()) return "";
        byte[] combined = Base64.decode(encoded, Base64.NO_WRAP);
        if (combined.length <= 12) throw new SecurityException("Credencial criptografada inválida.");
        byte[] iv = new byte[12];
        byte[] encrypted = new byte[combined.length - iv.length];
        System.arraycopy(combined, 0, iv, 0, iv.length);
        System.arraycopy(combined, iv.length, encrypted, 0, encrypted.length);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(), new GCMParameterSpec(128, iv));
        return new String(cipher.doFinal(encrypted), "UTF-8");
    }

    public static void clear(Context context) {
        prefs(context).edit().remove(KEY_CIPHER).apply();
    }

    private static SecretKey getOrCreateKey() throws Exception {
        KeyStore store = KeyStore.getInstance(ANDROID_KEY_STORE);
        store.load(null);
        java.security.Key existing = store.getKey(KEY_ALIAS, null);
        if (existing instanceof SecretKey) return (SecretKey) existing;
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEY_STORE);
        generator.init(new KeyGenParameterSpec.Builder(KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build());
        return generator.generateKey();
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
}
