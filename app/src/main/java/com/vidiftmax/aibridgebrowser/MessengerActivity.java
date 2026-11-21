package com.vidiftmax.aibridgebrowser;

import android.app.Activity;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.text.DateFormat;
import java.util.Date;

public final class MessengerActivity extends Activity {
    private static final String PREFS = "ai_messenger_local_v1";
    private static final String KEY_MESSAGES = "local_messages";
    private static final String CONVERSATION_ID = "LOCAL-DEMO";
    private static final int BG = 0xFF101827;
    private static final int SURFACE = 0xFF1B293B;
    private static final int TEXT = 0xFFF4F7FB;
    private static final int MUTED = 0xFFB5C2D1;
    private static final int ACCENT = 0xFF55D6BE;
    private LinearLayout messageList;
    private EditText composer;
    private TextView status;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(16), dp(14), dp(16), dp(12));
        page.setBackgroundColor(BG);

        TextView title = text("AI MESSENGER", 25, TEXT, true);
        page.addView(title);
        TextView subtitle = text("Conversa local de demonstração · sem destinatário conectado", 13, MUTED, false);
        page.addView(subtitle);
        status = text("LOCAL ONLY — mensagens ficam somente neste aparelho.", 12, ACCENT, true);
        status.setPadding(0, dp(8), 0, dp(8));
        page.addView(status);

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(false);
        messageList = new LinearLayout(this);
        messageList.setOrientation(LinearLayout.VERTICAL);
        messageList.setPadding(0, dp(6), 0, dp(10));
        scroll.addView(messageList);
        page.addView(scroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));

        LinearLayout entry = new LinearLayout(this);
        entry.setOrientation(LinearLayout.HORIZONTAL);
        composer = new EditText(this);
        composer.setHint("Escreva uma mensagem local...");
        composer.setTextColor(TEXT);
        composer.setHintTextColor(MUTED);
        composer.setMinLines(1);
        composer.setMaxLines(4);
        entry.addView(composer, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        Button send = new Button(this);
        send.setText("Salvar");
        send.setAllCaps(false);
        send.setOnClickListener(v -> saveLocalMessage());
        entry.addView(send);
        page.addView(entry);
        Button clear = new Button(this);
        clear.setText("Apagar histórico local");
        clear.setAllCaps(false);
        clear.setOnClickListener(v -> confirmClear());
        page.addView(clear);
        setContentView(page);
        renderMessages();
    }

    private void saveLocalMessage() {
        String body = composer.getText().toString().trim();
        if (body.isEmpty()) {
            Toast.makeText(this, "Digite uma mensagem primeiro.", Toast.LENGTH_SHORT).show();
            return;
        }
        try {
            MessengerMessage message = new MessengerMessage(
                    CONVERSATION_ID, "Este dispositivo", body, System.currentTimeMillis());
            JSONArray messages = readMessages();
            JSONObject item = new JSONObject();
            item.put("messageId", message.getMessageId());
            item.put("conversationId", message.getConversationId());
            item.put("senderLabel", message.getSenderLabel());
            item.put("body", message.getBody());
            item.put("createdAtEpochMs", message.getCreatedAtEpochMs());
            item.put("status", MessengerMessage.STATUS_LOCAL_ONLY);
            messages.put(item);
            getSharedPreferences(PREFS, MODE_PRIVATE).edit()
                    .putString(KEY_MESSAGES, messages.toString()).apply();
            composer.setText("");
            renderMessages();
        } catch (JSONException error) {
            Toast.makeText(this, "Não foi possível salvar a mensagem local.", Toast.LENGTH_LONG).show();
        }
    }

    private JSONArray readMessages() {
        String raw = getSharedPreferences(PREFS, MODE_PRIVATE).getString(KEY_MESSAGES, "[]");
        try { return new JSONArray(raw); }
        catch (JSONException invalid) { return new JSONArray(); }
    }

    private void renderMessages() {
        messageList.removeAllViews();
        JSONArray messages = readMessages();
        if (messages.length() == 0) {
            TextView empty = text("Nenhuma mensagem salva. Escreva abaixo para criar um registro LOCAL ONLY.", 14, MUTED, false);
            empty.setPadding(0, dp(18), 0, dp(18));
            messageList.addView(empty);
            return;
        }
        for (int i = 0; i < messages.length(); i++) {
            JSONObject item = messages.optJSONObject(i);
            if (item == null) continue;
            LinearLayout bubble = new LinearLayout(this);
            bubble.setOrientation(LinearLayout.VERTICAL);
            bubble.setPadding(dp(13), dp(10), dp(13), dp(10));
            GradientDrawable shape = new GradientDrawable();
            shape.setColor(SURFACE);
            shape.setCornerRadius(dp(14));
            bubble.setBackground(shape);
            TextView body = text(item.optString("body", ""), 15, TEXT, false);
            bubble.addView(body);
            long time = item.optLong("createdAtEpochMs", 0);
            String stamp = time > 0 ? DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT)
                    .format(new Date(time)) : "horário indisponível";
            bubble.addView(text(stamp + " · LOCAL ONLY", 11, ACCENT, true));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.bottomMargin = dp(9);
            messageList.addView(bubble, lp);
        }
    }

    private void confirmClear() {
        new android.app.AlertDialog.Builder(this)
                .setTitle("Apagar histórico local?")
                .setMessage("Isso remove as mensagens salvas somente neste aparelho. Nenhuma mensagem remota será afetada.")
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Apagar", (dialog, which) -> {
                    getSharedPreferences(PREFS, MODE_PRIVATE).edit().remove(KEY_MESSAGES).apply();
                    renderMessages();
                }).show();
    }

    private TextView text(String value, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        view.setPadding(0, dp(3), 0, dp(3));
        return view;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
