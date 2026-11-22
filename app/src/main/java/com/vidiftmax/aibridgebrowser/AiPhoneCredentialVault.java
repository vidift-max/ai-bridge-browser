package com.vidiftmax.aibridgebrowser;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Stores the bearer credential encrypted with a key held by Android Keystore. */
public final class AiPhoneCredentialVault {
    private static final String PREFS = "ai_phone_registry_secure_v1";
    private static final String KEY_ALIAS = "ai_phone_registry_token_key_v1";
    private static final String IV = "token_iv";
    private static final String DATA = "token_ciphertext";

    public void save(Context context, String token) throws Exception {
        if (token == null || token.trim().isEmpty()) throw new IllegalArgumentException("token_required");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey());
        byte[] encrypted = cipher.doFinal(token.trim().getBytes(StandardCharsets.UTF_8));
        SharedPreferences.Editor edit = prefs(context).edit();
        edit.putString(IV, Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP));
        edit.putString(DATA, Base64.encodeToString(encrypted, Base64.NO_WRAP));
        if (!edit.commit()) throw new IllegalStateException("Não foi possível salvar a credencial.");
    }

    public String load(Context context) throws Exception {
        SharedPreferences store = prefs(context);
        String ivText = store.getString(IV, null);
        String dataText = store.getString(DATA, null);
        if (ivText == null || dataText == null) return null;
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(),
                new GCMParameterSpec(128, Base64.decode(ivText, Base64.NO_WRAP)));
        return new String(cipher.doFinal(Base64.decode(dataText, Base64.NO_WRAP)),
                StandardCharsets.UTF_8);
    }

    public void clear(Context context) {
        prefs(context).edit().clear().commit();
    }

    private SecretKey getOrCreateKey() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        java.security.Key existing = store.getKey(KEY_ALIAS, null);
        if (existing instanceof SecretKey) return (SecretKey) existing;
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build());
        return generator.generateKey();
    }

    private SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
}
