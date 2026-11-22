package com.vidiftmax.aibridgebrowser;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Participant-facing screen for securely retrieving the server-assigned phone number. */
public final class AiPhoneRegistryActivity extends Activity {
    private static final String PREFS = "ai_phone_registry_connection_v1";
    private static final String KEY_URL = "base_url";
    private static final String KEY_TOKEN = "bearer_token";
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());
    private TextView connectionState;
    private TextView identityCard;
    private Button connectButton;
    private boolean loading;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(0xFF101827);
        getWindow().setNavigationBarColor(0xFF101827);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(20), dp(24), dp(20), dp(24));
        page.setBackgroundColor(0xFF101827);

        TextView title = text("MEU NÚMERO AI-PHONE", 25, 0xFFF4F7FB, true);
        page.addView(title);
        page.addView(text("O número é atribuído pelo registro central e permanece vinculado à identidade autenticada.", 14, 0xFFB5C2D1, false));
        connectionState = text("Servidor ainda não configurado.", 14, 0xFFFFD18A, true);
        connectionState.setPadding(0, dp(18), 0, dp(12));
        page.addView(connectionState);

        identityCard = text("Número: ainda não consultado\n\nAI_ID: não verificado\nSérie: não provisionada\nEstado: NÃO CONECTADO", 17, 0xFFF4F7FB, true);
        identityCard.setPadding(dp(16), dp(18), dp(16), dp(18));
        identityCard.setBackgroundColor(0xFF1B293B);
        page.addView(identityCard, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        connectButton = new Button(this);
        connectButton.setText("Consultar meu número");
        connectButton.setAllCaps(false);
        connectButton.setOnClickListener(v -> connect());
        page.addView(connectButton, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        Button settings = new Button(this);
        settings.setText("Configurar servidor e credencial");
        settings.setAllCaps(false);
        settings.setOnClickListener(v -> showSettings());
        page.addView(settings, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        page.addView(text("A credencial é armazenada somente nas preferências privadas deste aplicativo. Nunca cole tokens em relatórios ou mensagens. A conexão exige HTTPS.", 12, 0xFFB5C2D1, false));
        ScrollView scroll = new ScrollView(this);
        scroll.addView(page);
        setContentView(scroll);
        if (hasConfiguration()) {
            connectionState.setText("Servidor configurado. Pronto para consultar a identidade autenticada.");
        }
    }

    private void showSettings() {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(dp(8), dp(4), dp(8), 0);
        EditText url = new EditText(this);
        url.setSingleLine(true);
        url.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        url.setHint("https://seu-servidor.example");
        url.setText(prefs().getString(KEY_URL, ""));
        form.addView(url);
        EditText token = new EditText(this);
        token.setSingleLine(true);
        token.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        token.setHint("Token Bearer (não será exibido novamente)");
        form.addView(token);
        new AlertDialog.Builder(this).setTitle("Conexão com o registro")
                .setMessage("O servidor deve ter o endpoint /v1/me/phone e reconhecer esta credencial.")
                .setView(form).setNegativeButton("Cancelar", null)
                .setPositiveButton("Salvar", (dialog, which) -> {
                    try {
                        String base = AiPhoneRegistryConfig.normalizeBaseUrl(url.getText().toString());
                        String secret = token.getText().toString().trim();
                        if (secret.isEmpty() && prefs().getString(KEY_TOKEN, "").isEmpty()) {
                            throw new IllegalArgumentException("Informe o token de acesso.");
                        }
                        android.content.SharedPreferences.Editor edit = prefs().edit().putString(KEY_URL, base);
                        if (!secret.isEmpty()) edit.putString(KEY_TOKEN, secret);
                        edit.apply();
                        connectionState.setText("Configuração salva localmente. Toque em Consultar meu número.");
                    } catch (IllegalArgumentException error) {
                        Toast.makeText(this, error.getMessage(), Toast.LENGTH_LONG).show();
                    }
                }).show();
    }

    private void connect() {
        if (loading) return;
        String base = prefs().getString(KEY_URL, "");
        String token = prefs().getString(KEY_TOKEN, "");
        if (base.isEmpty() || token.isEmpty()) {
            showSettings();
            return;
        }
        loading = true;
        connectButton.setEnabled(false);
        connectionState.setText("Consultando registro seguro…");
        executor.execute(() -> {
            try {
                AiPhoneIdentity identity = AiPhoneRegistryClient.fetchMyPhone(base, token);
                main.post(() -> showIdentity(identity));
            } catch (Exception error) {
                String message = error.getMessage() == null ? "Falha de conexão." : error.getMessage();
                main.post(() -> {
                    connectionState.setText("Não foi possível confirmar o número: " + message);
                    Toast.makeText(this, message, Toast.LENGTH_LONG).show();
                    finishLoading();
                });
            }
        });
    }

    private void showIdentity(AiPhoneIdentity identity) {
        connectionState.setText("Identidade confirmada pelo servidor · HTTPS · registro ACTIVE");
        identityCard.setText("Número: " + identity.getDisplayNumber() +
                "\n\nParticipante: " + identity.getDisplayName() +
                "\nAI_ID: " + identity.getAiId() +
                "\nSérie: " + identity.getSerial() +
                "\nProvedor: " + identity.getProvider() +
                "\nEstado: " + identity.getStatus().name());
        finishLoading();
    }

    private void finishLoading() {
        loading = false;
        connectButton.setEnabled(true);
    }

    private boolean hasConfiguration() {
        return !prefs().getString(KEY_URL, "").isEmpty() &&
                !prefs().getString(KEY_TOKEN, "").isEmpty();
    }

    private android.content.SharedPreferences prefs() {
        return getSharedPreferences(PREFS, MODE_PRIVATE);
    }

    @Override protected void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
    }

    private TextView text(String value, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        view.setPadding(0, dp(6), 0, dp(6));
        return view;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
