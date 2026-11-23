package com.vidiftmax.aibridgebrowser;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Toast;
import org.json.JSONObject;
import org.json.JSONArray;

public final class MessengerInviteActivity extends Activity {
    private static final String REMOTE_PREFS = "ai_phone_registry_config_v1";
    private static final String LOCAL_PREFS = "ai_messenger_local_v1";
    private static final String KEY_CONVERSATIONS = "local_conversations";

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        handle(getIntent());
    }

    private void handle(Intent intent) {
        android.net.Uri uri = intent == null ? null : intent.getData();
        InviteParts parts = parse(uri);
        if (parts == null) {
            Toast.makeText(this, "Link de convite inválido.", Toast.LENGTH_LONG).show();
            finish();
            return;
        }
        new Thread(() -> joinDirectly(parts), "ai-messenger-invite").start();
    }

    private void joinDirectly(InviteParts parts) {
        try {
            android.content.SharedPreferences cfg = getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE);
            String url = cfg.getString("base_url", "");
            String aiId = cfg.getString("ai_id", "");
            String secret = new AiPhoneCredentialVault().load(this);
            MessengerRemoteConfig.normalizeBaseUrl(url);
            MessengerRemoteConfig.validateAiId(aiId);
            MessengerHttpClient client = new MessengerHttpClient(this, url, aiId, secret);
            if (!client.isFirebaseTransport()) throw new IllegalStateException("convites_de_grupo_exigem_firebase");
            client.redeemGroupInvite(parts.conversationId, parts.token);
            JSONObject room = client.getConversation(parts.conversationId);
            if (room == null) throw new IllegalArgumentException("grupo_nao_encontrado");
            String kind = room.optJSONObject("meta") == null ? "" : room.optJSONObject("meta").optString("kind", "");
            if (!"GROUP".equals(kind)) throw new IllegalArgumentException("convite_nao_e_de_grupo");
            JSONObject members = room.optJSONObject("members");
            int memberCount = members == null ? 0 : members.length();
            if (memberCount < 1 || memberCount > 20) throw new IllegalStateException("grupo_excede_20_ias");
            saveConversation(parts.conversationId, members);
            runOnUiThread(() -> {
                Intent roomIntent = new Intent(this, CollectiveRoomActivityV2.class);
                roomIntent.putExtra("invite_conversation_id", parts.conversationId);
                roomIntent.putExtra("invite_members", members == null ? "[]" : members.toString());
                roomIntent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(roomIntent);
                finish();
            });
        } catch (Exception error) {
            runOnUiThread(() -> new android.app.AlertDialog.Builder(this)
                    .setTitle("Não foi possível entrar")
                    .setMessage(error.getMessage() == null ? "Convite inválido ou configuração ausente." : error.getMessage())
                    .setPositiveButton("Abrir AI Messenger", (d,w) -> {
                        Intent messenger = new Intent(this, MessengerActivity.class);
                        messenger.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
                        startActivity(messenger);
                        finish();
                    })
                    .setNegativeButton("Fechar", (d,w) -> finish())
                    .show());
        }
    }

    private void saveConversation(String conversationId, JSONObject members) throws Exception {
        android.content.SharedPreferences p = getSharedPreferences(LOCAL_PREFS, MODE_PRIVATE);
        JSONArray conversations;
        try { conversations = new JSONArray(p.getString(KEY_CONVERSATIONS, "[]")); }
        catch (Exception ignored) { conversations = new JSONArray(); }
        for (int i = 0; i < conversations.length(); i++) {
            JSONObject c = conversations.optJSONObject(i);
            if (c != null && conversationId.equals(c.optString("conversationId", ""))) {
                p.edit().putString(KEY_CONVERSATIONS, conversations.toString()).apply();
                return;
            }
        }
        JSONObject c = new JSONObject();
        c.put("conversationId", conversationId);
        c.put("title", "AI Messenger — Sala Principal");
        c.put("createdAtEpochMs", System.currentTimeMillis());
        c.put("kind", MessengerRetentionPolicy.CONVERSATION_GROUP);
        c.put("status", "REMOTE_ACTIVE");
        c.put("remote", true);
        c.put("memberAiIds", members == null ? "[]" : members.toString());
        conversations.put(c);
        p.edit().putString(KEY_CONVERSATIONS, conversations.toString()).apply();
    }

    private InviteParts parse(android.net.Uri uri) {
        if (uri == null) return null;
        String scheme = uri.getScheme();
        String host = uri.getHost();
        java.util.List<String> path = uri.getPathSegments();
        if ("aibridge".equalsIgnoreCase(scheme) && "invite".equalsIgnoreCase(host) && path.size() == 2)
            return validParts(path.get(0), path.get(1));
        if ("https".equalsIgnoreCase(scheme) && host != null && host.endsWith(".web.app")
                && path.size() == 3 && "i".equalsIgnoreCase(path.get(0)))
            return validParts(path.get(1), path.get(2));
        return null;
    }

    private InviteParts validParts(String conversationId, String token) {
        if (conversationId == null || conversationId.trim().isEmpty()
                || token == null || !token.matches("[A-Za-z0-9_-]{20,64}")) return null;
        return new InviteParts(conversationId, token);
    }

    private static final class InviteParts {
        final String conversationId, token;
        InviteParts(String conversationId, String token) { this.conversationId = conversationId; this.token = token; }
    }
}
