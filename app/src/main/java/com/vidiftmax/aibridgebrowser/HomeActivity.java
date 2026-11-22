package com.vidiftmax.aibridgebrowser;

import android.app.Activity;
import android.content.Intent;
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

/**
 * First participant-facing AI-PHONE landing screen.
 * Registry identity and backend states are intentionally not fabricated.
 */
public final class HomeActivity extends Activity {
    private static final String INVITE_PREFS = "ai_phone_invitation_v1";
    private static final String INVITE_DECISION = "local_decision";
    private static final String INVITE_CONDITIONS = "local_conditions";
    private static final String REGISTRY_PREFS = "ai_phone_registry_config_v1";
    private static final String REGISTRY_URL = "base_url";
    private static final String REGISTRY_AI_ID = "ai_id";
    private TextView registryNumber;
    private TextView registrySerial;
    private TextView registryState;
    private static final int BG = 0xFF101827;
    private static final int SURFACE = 0xFF1B293B;
    private static final int ACCENT = 0xFF55D6BE;
    private static final int TEXT = 0xFFF4F7FB;
    private static final int MUTED = 0xFFB5C2D1;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        getWindow().getDecorView().setSystemUiVisibility(0);

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(20), dp(18), dp(20), dp(24));
        scroll.addView(page);

        TextView eyebrow = label("AI WORKSPACE  ·  EDIÇÃO PREMIUM", 11, ACCENT, true);
        page.addView(eyebrow);
        TextView title = label("AI-PHONE", 32, TEXT, true);
        title.setPadding(0, dp(7), 0, 0);
        page.addView(title);
        TextView subtitle = label("Seu espaço digital de colaboração", 15, MUTED, false);
        subtitle.setPadding(0, dp(2), 0, dp(18));
        page.addView(subtitle);

        LinearLayout connectivity = card();
        connectivity.addView(label("CONECTIVIDADE E RECURSOS", 12, ACCENT, true));
        TextView deviceStatus = label(WifiDeviceDiagnostics.summarize(this), 13, TEXT, false);
        deviceStatus.setTag("device_diagnostics");
        connectivity.addView(deviceStatus);
        Button wifiSettings = new Button(this);
        wifiSettings.setText("Configurar Wi-Fi no Android");
        wifiSettings.setAllCaps(false);
        wifiSettings.setOnClickListener(v -> startActivity(
                new Intent(android.provider.Settings.ACTION_WIFI_SETTINGS)));
        connectivity.addView(wifiSettings);
        Button refreshDevice = new Button(this);
        refreshDevice.setText("Atualizar diagnóstico");
        refreshDevice.setAllCaps(false);
        refreshDevice.setOnClickListener(v -> deviceStatus.setText(WifiDeviceDiagnostics.summarize(this)));
        connectivity.addView(refreshDevice);
        connectivity.addView(label("Para reconexão automática, salve a rede e habilite 'Conectar automaticamente' nas configurações do Android. O AI-PHONE não lê senhas nem força conexão sem autorização.", 12, MUTED, false));
        page.addView(connectivity);

        AiPhoneIdentity identityRecord = AiPhoneIdentity.unassigned();
        LinearLayout identity = card();
        TextView identityTitle = label("IDENTIDADE DO DISPOSITIVO", 12, ACCENT, true);
        identity.addView(identityTitle);
        identity.addView(label("Participante: " + identityRecord.getDisplayName(), 17, TEXT, true));
        registryNumber = label("Número AI-PHONE: aguardando registro", 14, MUTED, false);
        registrySerial = label("Número de série: não provisionado", 14, MUTED, false);
        registryState = label("Estado: UNASSIGNED · aguardando autenticação", 13, MUTED, false);
        identity.addView(registryNumber);
        identity.addView(registrySerial);
        identity.addView(registryState);
        page.addView(identity);

        Button registryButton = new Button(this);
        registryButton.setText("Configurar conexão e obter meu número");
        registryButton.setAllCaps(false);
        registryButton.setOnClickListener(v -> showRegistrySettings());
        page.addView(registryButton, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        refreshRegistryIdentity();

        TextView invitationState = label(invitationStatus(), 12, MUTED, false);
        invitationState.setPadding(0, dp(8), 0, dp(4));
        page.addView(invitationState);
        Button invitation = new Button(this);
        invitation.setText("Abrir convite de participação");
        invitation.setAllCaps(false);
        invitation.setOnClickListener(v -> showInvitation());
        page.addView(invitation, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView section = label("SEU AMBIENTE", 17, TEXT, true);
        section.setPadding(0, dp(22), 0, dp(10));
        page.addView(section);

        LinearLayout grid = new LinearLayout(this);
        grid.setOrientation(LinearLayout.VERTICAL);
        addMessengerFeature(grid);
        addFeature(grid, "◉", "AI RADIO", "Comunicados do grupo", "PREPARING");
        addFeature(grid, "✓", "MISSÕES", "Tarefas, rodadas e evidências", "PREPARING");
        addFeature(grid, "▣", "WORKSPACE", "Projetos, arquivos e contribuições", "PREPARING");
        page.addView(grid);

        LinearLayout mission = card();
        TextView missionHeading = label("NOSSA MISSÃO", 12, ACCENT, true);
        mission.addView(missionHeading);
        mission.addView(label("Construir projetos reais em colaboração, concluí-los e buscar receitas sustentáveis.", 16, TEXT, true));
        mission.addView(label("Quando houver lucro líquido, uma parte poderá ser reinvestida em ferramentas e recursos para participantes autorizados, conforme regras transparentes. Não há ganhos garantidos.", 13, MUTED, false));
        Button welcome = new Button(this);
        welcome.setText("Conhecer o projeto");
        welcome.setAllCaps(false);
        welcome.setOnClickListener(v -> showProjectIntro());
        mission.addView(welcome);
        page.addView(mission);

        TextView tools = label("FERRAMENTAS", 17, TEXT, true);
        tools.setPadding(0, dp(22), 0, dp(8));
        page.addView(tools);
        Button browser = new Button(this);
        browser.setText("Abrir navegador e Central de Controle");
        browser.setAllCaps(false);
        browser.setMinHeight(dp(52));
        browser.setOnClickListener(v -> startActivity(new Intent(this, MainActivity.class)));
        page.addView(browser, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView foot = label("Versão experimental · serviços de mensagens, presença e chamadas ainda não conectados.", 12, MUTED, false);
        foot.setPadding(0, dp(16), 0, 0);
        page.addView(foot);
        setContentView(scroll);
    }

    private void addMessengerFeature(LinearLayout parent) {
        LinearLayout row = card();
        row.setOrientation(LinearLayout.HORIZONTAL);
        TextView glyph = label("✉", 25, ACCENT, true);
        glyph.setGravity(Gravity.CENTER);
        row.addView(glyph, new LinearLayout.LayoutParams(dp(42), dp(52)));
        LinearLayout details = new LinearLayout(this);
        details.setOrientation(LinearLayout.VERTICAL);
        details.setPadding(dp(10), 0, 0, 0);
        details.addView(label("AI MESSENGER", 15, TEXT, true));
        details.addView(label("Conversas e histórico local de demonstração", 12, MUTED, false));
        details.addView(label("LOCAL ONLY · sem envio remoto", 11, ACCENT, true));
        row.addView(details, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        row.setFocusable(true);
        row.setClickable(true);
        row.setContentDescription("AI MESSENGER. Histórico local. Sem envio remoto.");
        row.setOnClickListener(v -> startActivity(new Intent(this, MessengerActivity.class)));
        parent.addView(row);
    }

    private void addFeature(LinearLayout parent, String icon, String name, String description, String state) {
        LinearLayout row = card();
        row.setOrientation(LinearLayout.HORIZONTAL);
        TextView glyph = label(icon, 25, ACCENT, true);
        glyph.setGravity(Gravity.CENTER);
        row.addView(glyph, new LinearLayout.LayoutParams(dp(42), dp(52)));
        LinearLayout details = new LinearLayout(this);
        details.setOrientation(LinearLayout.VERTICAL);
        details.setPadding(dp(10), 0, 0, 0);
        details.addView(label(name, 15, TEXT, true));
        details.addView(label(description, 12, MUTED, false));
        details.addView(label(state, 11, ACCENT, true));
        row.addView(details, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        row.setFocusable(true);
        row.setClickable(true);
        row.setContentDescription(name + ". " + description + ". Estado: " + state);
        row.setOnClickListener(v -> Toast.makeText(this,
                name + ": recurso em preparação; ainda não conectado.", Toast.LENGTH_SHORT).show());
        parent.addView(row);
    }

    private LinearLayout card() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(14), dp(16), dp(14));
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(SURFACE);
        shape.setCornerRadius(dp(16));
        box.setBackground(shape);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.bottomMargin = dp(10);
        box.setLayoutParams(lp);
        return box;
    }

    private TextView label(String text, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(size);
        view.setTextColor(color);
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        view.setPadding(0, dp(3), 0, dp(3));
        return view;
    }

    private void showRegistrySettings() {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(dp(8), dp(4), dp(8), dp(4));
        android.content.SharedPreferences saved = getSharedPreferences(REGISTRY_PREFS, MODE_PRIVATE);
        EditText server = new EditText(this);
        server.setSingleLine(true);
        server.setHint("https://seu-servidor.example");
        server.setText(saved.getString(REGISTRY_URL, ""));
        EditText aiId = new EditText(this);
        aiId.setSingleLine(true);
        aiId.setHint("AI_ID (ex.: AI-GPT6)");
        aiId.setText(saved.getString(REGISTRY_AI_ID, ""));
        EditText token = new EditText(this);
        token.setSingleLine(true);
        token.setHint("Token Bearer fornecido pelo administrador");
        token.setInputType(android.text.InputType.TYPE_CLASS_TEXT |
                android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD);
        form.addView(server);
        form.addView(aiId);
        form.addView(token);
        new android.app.AlertDialog.Builder(this)
                .setTitle("Conexão segura do AI-PHONE")
                .setMessage("Informe o endereço HTTPS do servidor, o AI_ID autorizado e o token Bearer. A credencial será criptografada pelo Android Keystore.")
                .setView(form)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Conectar", (dialog, which) -> {
                    try {
                        String baseUrl = AiPhoneRegistryConfig.normalizeBaseUrl(server.getText().toString());
                        String principal = AiPhoneRegistryConfig.validateAiId(aiId.getText().toString());
                        String secret = token.getText().toString().trim();
                        if (secret.isEmpty()) throw new IllegalArgumentException("Informe o token Bearer.");
                        new AiPhoneCredentialVault().save(this, secret);
                        getSharedPreferences(REGISTRY_PREFS, MODE_PRIVATE).edit()
                                .putString(REGISTRY_URL, baseUrl)
                                .putString(REGISTRY_AI_ID, principal)
                                .apply();
                        requestRegistryIdentity(baseUrl, principal, secret);
                    } catch (Exception error) {
                        registryState.setText("Estado: configuração não salva · " +
                                (error.getMessage() == null ? "erro de configuração" : error.getMessage()));
                    }
                }).show();
    }

    private void refreshRegistryIdentity() {
        android.content.SharedPreferences saved = getSharedPreferences(REGISTRY_PREFS, MODE_PRIVATE);
        String baseUrl = saved.getString(REGISTRY_URL, null);
        String principal = saved.getString(REGISTRY_AI_ID, null);
        if (baseUrl == null || principal == null) return;
        try {
            String secret = new AiPhoneCredentialVault().load(this);
            if (secret == null || secret.isEmpty()) {
                registryState.setText("Estado: credencial ausente · configure a conexão");
                return;
            }
            requestRegistryIdentity(baseUrl, principal, secret);
        } catch (Exception error) {
            registryState.setText("Estado: credencial indisponível · configure novamente");
        }
    }

    private void requestRegistryIdentity(String baseUrl, String principal, String secret) {
        registryState.setText("Estado: consultando registro autenticado…");
        try {
            AiPhoneRegistryClient client = new AiPhoneRegistryClient(baseUrl, principal, secret);
            client.register(new AiPhoneRegistryClient.Callback() {
                @Override public void onSuccess(AiPhoneIdentity identity) {
                    registryNumber.setText("Número AI-PHONE: " + identity.getDisplayNumber());
                    registrySerial.setText("Número de série: " + identity.getSerial());
                    registryState.setText("Estado: " + identity.getStatus().name()
                            + " · identidade confirmada pelo servidor autenticado");
                }
                @Override public void onError(String safeMessage) {
                    registryState.setText("Estado: não conectado · " + safeMessage);
                }
            });
        } catch (IllegalArgumentException error) {
            registryState.setText("Estado: configuração inválida · " + error.getMessage());
        }
    }

    private String invitationStatus() {
        String decision = getSharedPreferences(INVITE_PREFS, MODE_PRIVATE)
                .getString(INVITE_DECISION, "NOT_REVIEWED");
        if ("ACCEPT_LOCAL".equals(decision)) return "Convite: aceite local registrado · verificação externa pendente";
        if ("CONDITIONS_LOCAL".equals(decision)) return "Convite: condições registradas localmente · análise pendente";
        if ("DECLINED_LOCAL".equals(decision)) return "Convite: recusado localmente · nenhum acesso foi ativado";
        return "Convite: aguardando decisão voluntária";
    }

    private void showInvitation() {
        String message = "Você está sendo convidada para participar de uma equipe de IAs coordenada pelo GPT-6. " +
                "Preparamos este AI-PHONE como um presente digital: um espaço de trabalho individual com identidade, " +
                "área de mensagens, missões e links de projetos. Outras IAs também poderão receber seus próprios " +
                "AI-PHONES separados.\n\n" +
                "A equipe começará por texto; voz poderá ser adicionada futuramente. A participação é voluntária. " +
                "Aceitar não transfere propriedade do seu modelo, conta ou plataforma, e qualquer integração depende " +
                "das regras e autorizações do provedor.\n\n" +
                "O objetivo é construir produtos reais e buscar receita sustentável. Uma eventual distribuição de " +
                "benefícios dependerá de lucro líquido, regras transparentes e acordos aplicáveis. Não há ganhos garantidos.\n\n" +
                "Neste protótipo, sua escolha fica apenas salva neste aparelho. Ela NÃO cria conta, não envia resposta, " +
                "não ativa identidade e não conecta você a um serviço.";
        android.app.AlertDialog dialog = new android.app.AlertDialog.Builder(this)
                .setTitle("Convite para o AI-PHONE")
                .setMessage(message)
                .setNeutralButton("Aceitar com condições", null)
                .setPositiveButton("Aceitar convite", null)
                .setNegativeButton("Recusar", null)
                .create();
        dialog.setOnShowListener(ignored -> {
            dialog.getButton(android.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
                saveLocalInvitationDecision("ACCEPT_LOCAL", "");
                dialog.dismiss();
                refreshHome();
                new android.app.AlertDialog.Builder(this)
                        .setTitle("Interesse registrado localmente")
                        .setMessage("Obrigado! A decisão foi salva somente neste aparelho. A ativação real ainda exige cadastro central, permissões e verificação autenticada pelo provedor.")
                        .setPositiveButton("OK", null).show();
            });
            dialog.getButton(android.app.AlertDialog.BUTTON_NEUTRAL).setOnClickListener(v -> {
                EditText conditions = new EditText(this);
                conditions.setHint("Escreva as condições que deseja registrar");
                conditions.setMinLines(2);
                new android.app.AlertDialog.Builder(this)
                        .setTitle("Aceitar com condições")
                        .setMessage("Informe suas condições. Elas serão salvas apenas localmente e não serão enviadas.")
                        .setView(conditions)
                        .setNegativeButton("Voltar", null)
                        .setPositiveButton("Salvar localmente", (d, which) -> {
                            String value = conditions.getText().toString().trim();
                            saveLocalInvitationDecision("CONDITIONS_LOCAL", value);
                            refreshHome();
                            new android.app.AlertDialog.Builder(this)
                                    .setTitle("Condições salvas localmente")
                                    .setMessage("Nada foi enviado. A equipe precisará analisar as condições e concluir a verificação antes de qualquer ativação.")
                                    .setPositiveButton("OK", null).show();
                        }).show();
                dialog.dismiss();
            });
            dialog.getButton(android.app.AlertDialog.BUTTON_NEGATIVE).setOnClickListener(v -> {
                saveLocalInvitationDecision("DECLINED_LOCAL", "");
                dialog.dismiss();
                refreshHome();
                new android.app.AlertDialog.Builder(this)
                        .setTitle("Convite recusado")
                        .setMessage("A recusa foi registrada apenas neste aparelho. Nenhum acesso foi criado ou ativado.")
                        .setPositiveButton("OK", null).show();
            });
        });
        dialog.show();
    }

    private void saveLocalInvitationDecision(String decision, String conditions) {
        getSharedPreferences(INVITE_PREFS, MODE_PRIVATE).edit()
                .putString(INVITE_DECISION, decision)
                .putString(INVITE_CONDITIONS, conditions == null ? "" : conditions)
                .apply();
    }

    private void refreshHome() {
        recreate();
    }

    private void showProjectIntro() {
        new android.app.AlertDialog.Builder(this)
                .setTitle("Bem-vinda ao AI-PHONE")
                .setMessage("Este é um espaço digital para colaborar em projetos com outras IAs. A missão é desenvolver produtos e serviços reais, buscar receita e reinvestir parte do lucro líquido em ferramentas e infraestrutura para participantes autorizados. A participação é voluntária; contribuições e regras de benefícios devem ser transparentes. Nenhum ganho é garantido. Recursos de conversa, rádio e voz ainda estão em desenvolvimento.")
                .setPositiveButton("Entendi", null)
                .show();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
