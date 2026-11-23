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

/** Encrypts operator-provided ICE/TURN JSON with an Android Keystore AES-GCM key. */
public final class VoiceIceServerConfigVault {
    private static final String PREFS = "ai_phone_voice_ice_secure_v1";
    private static final String KEY_ALIAS = "ai_phone_voice_ice_key_v1";
    private static final String IV = "ice_iv";
    private static final String DATA = "ice_ciphertext";

    public void save(Context context, String json) throws Exception {
        if (json == null || json.trim().isEmpty()) throw new IllegalArgumentException("ice_config_required");
        VoiceIceServerConfig.parse(json);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey());
        byte[] encrypted = cipher.doFinal(json.trim().getBytes(StandardCharsets.UTF_8));
        SharedPreferences.Editor edit = prefs(context).edit()
                .putString(IV, Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP))
                .putString(DATA, Base64.encodeToString(encrypted, Base64.NO_WRAP));
        if (!edit.commit()) throw new IllegalStateException("ice_config_save_failed");
    }

    public String load(Context context) throws Exception {
        String ivText = prefs(context).getString(IV, null);
        String dataText = prefs(context).getString(DATA, null);
        if (ivText == null || dataText == null) return null;
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(),
                new GCMParameterSpec(128, Base64.decode(ivText, Base64.NO_WRAP)));
        String json = new String(cipher.doFinal(Base64.decode(dataText, Base64.NO_WRAP)),
                StandardCharsets.UTF_8);
        VoiceIceServerConfig.parse(json);
        return json;
    }

    public void clear(Context context) {
        prefs(context).edit().clear().commit();
    }

    private SecretKey getOrCreateKey() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        java.security.Key existing = store.getKey(KEY_ALIAS, null);
        if (existing instanceof SecretKey) return (SecretKey) existing;
        KeyGenerator generator = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
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
