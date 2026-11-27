package com.vidiftmax.aibridgebrowser;

import android.app.Activity;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONObject;

public final class Gpt6Activity extends Activity {
    private static final int BG = 0xFF101827;
    private static final int TEXT = 0xFFF4F7FB;
    private static final int MUTED = 0xFFB5C2D1;
    private static final int ACCENT = 0xFF55D6BE;
    private static final String REMOTE_PREFS = "ai_phone_registry_config_v1";
    private static final String GPT6_RESPONSE = "gpt6_previous_response_id";
    private LinearLayout transcript;
    private EditText composer;
    private TextView status;
    private android.content.SharedPreferences prefs;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(24, 18, 24, 18);
        page.setBackgroundColor(BG);

        TextView title = text("GPT-6 · AI MESSENGER", 24, TEXT, true);
        page.addView(title);
        status = text("Verificando conexão…", 13, MUTED, false);
        page.addView(status);

        ScrollView scroll = new ScrollView(this);
        transcript = new LinearLayout(this);
        transcript.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(transcript);
        page.addView(scroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));

        LinearLayout entry = new LinearLayout(this);
        composer = new EditText(this);
        composer.setHint("Fale comigo por texto…");
        composer.setTextColor(TEXT);
        composer.setHintTextColor(MUTED);
        composer.setMaxLines(5);
        entry.addView(composer, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        Button send = new Button(this);
        send.setText("Enviar");
        send.setAllCaps(false);
        send.setOnClickListener(v -> send());
        entry.addView(send);
        page.addView(entry);

        Button reset = new Button(this);
        reset.setText("Nova conversa com GPT-6");
        reset.setAllCaps(false);
        reset.setOnClickListener(v -> {
            prefs.edit().remove(GPT6_RESPONSE).apply();
            transcript.removeAllViews();
            status.setText("Nova conversa criada localmente.");
        });
        page.addView(reset);

        setContentView(page);
        checkStatus();
    }

    private void checkStatus() {
        new Thread(() -> {
            try {
                JSONObject response = client().getGpt6Status();
                JSONObject assistant = response.getJSONObject("assistant");
                boolean online = assistant.optBoolean("online", false);
                runOnUiThread(() -> status.setText(online
                        ? "● GPT-6 online · " + response.optString("model", "modelo configurado")
                        : "○ GPT-6 offline · servidor sem API OpenAI configurada"));
            } catch (Exception e) {
                runOnUiThread(() -> status.setText("○ GPT-6 indisponível · " + e.getMessage()));
            }
        }).start();
    }

    private void send() {
        String message = composer.getText().toString().trim();
        if (message.isEmpty()) return;
        composer.setEnabled(false);
        addLine("Você", message, TEXT);
        composer.setText("");
        final String previous = prefs.getString(GPT6_RESPONSE, null);
        new Thread(() -> {
            try {
                JSONObject response = client().sendToGpt6(message, previous);
                String answer = response.optString("text", "");
                String responseId = response.optString("responseId", "");
                if (!responseId.isEmpty()) prefs.edit().putString(GPT6_RESPONSE, responseId).apply();
                runOnUiThread(() -> {
                    addLine("GPT-6", answer, ACCENT);
                    status.setText("● GPT-6 online · resposta recebida");
                    composer.setEnabled(true);
                    composer.requestFocus();
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    addLine("Sistema", "Não consegui conectar ao GPT-6: " + e.getMessage(), MUTED);
                    status.setText("○ GPT-6 offline/indisponível");
                    composer.setEnabled(true);
                });
            }
        }).start();
    }

    private MessengerHttpClient client() throws Exception {
        android.content.SharedPreferences p = getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE);
        return new MessengerHttpClient(p.getString("base_url", null), p.getString("ai_id", null),
                new AiPhoneCredentialVault().load(this));
    }

    private void addLine(String who, String body, int color) {
        TextView line = text(who + ": " + body, 15, color, false);
        line.setPadding(0, 10, 0, 10);
        transcript.addView(line);
    }

    private TextView text(String value, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return view;
    }
}
