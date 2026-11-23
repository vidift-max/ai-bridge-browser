package com.vidiftmax.aibridgebrowser;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Toast;
import org.json.JSONObject;

public final class MessengerInviteActivity extends Activity {
    private static final String REMOTE_PREFS = "ai_phone_registry_config_v1";

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        handle(getIntent());
    }

    private void handle(Intent intent) {
        android.net.Uri uri = intent == null ? null : intent.getData();
        if (uri == null || !"aibridge".equalsIgnoreCase(uri.getScheme())
                || !"invite".equalsIgnoreCase(uri.getHost()) || uri.getPathSegments().size() != 2) {
            Toast.makeText(this, "Link de convite inválido.", Toast.LENGTH_LONG).show();
            finish();
            return;
        }
        String conversationId = uri.getPathSegments().get(0);
        String token = uri.getPathSegments().get(1);
        new Thread(() -> {
            try {
                android.content.SharedPreferences cfg = getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE);
                String url = cfg.getString("base_url", "");
                String aiId = cfg.getString("ai_id", "");
                String secret = new AiPhoneCredentialVault().load(this);
                MessengerRemoteConfig.normalizeBaseUrl(url);
                MessengerRemoteConfig.validateAiId(aiId);
                FirebaseMessengerClient client = new FirebaseMessengerClient(this, url, secret, aiId);
                client.redeemGroupInvite(conversationId, token);
                runOnUiThread(() -> {
                    Toast.makeText(this, "Você entrou na sala pelo convite.", Toast.LENGTH_LONG).show();
                    Intent room = new Intent(this, CollectiveRoomActivityV2.class);
                    room.putExtra("invite_conversation_id", conversationId);
                    room.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                    startActivity(room);
                    finish();
                });
            } catch (Exception error) {
                runOnUiThread(() -> {
                    new android.app.AlertDialog.Builder(this)
                            .setTitle("Não foi possível entrar")
                            .setMessage(error.getMessage() == null ? "Convite inválido ou configuração ausente." : error.getMessage())
                            .setPositiveButton("Abrir AI Messenger", (d,w) ->
                                    startActivity(new Intent(this, MessengerActivity.class)))
                            .setNegativeButton("Fechar", null).show();
                });
            }
        }, "ai-messenger-invite").start();
    }
}
