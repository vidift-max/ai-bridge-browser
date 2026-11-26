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

import java.io.BufferedReader;
import java.io.InputStreamReader;

/**
 * First participant-facing AI-PHONE landing screen.
 * Registry identity and backend states are intentionally not fabricated.
 */
public final class HomeActivity extends Activity {
    private static final String INVITE_PREFS = "ai_phone_invitation_v1";
    private static final String INVITE_DECISION = "local_decision";
    private static final String INVITE_CONDITIONS = "local_conditions";
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
        scroll.setBackground(createPremiumWallpaper());
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

        LinearLayout identity = card();
        identity.addView(label("IDENTIDADE DA IA", 12, ACCENT, true));
        identity.addView(label("Sem número telefônico. O AI_ID será exibido somente após associação e autenticação central.", 13, MUTED, false));
        page.addView(identity);

        LinearLayout sounds = card();
        sounds.addView(label("TOQUES DO AI-PHONE", 12, ACCENT, true));
        sounds.addView(label("Sons integrados ao aplicativo, sem arquivos externos. Escolha um estilo para ouvir.", 12, MUTED, false));
        addSoundButton(sounds, "Mensagem", "Toque curto e discreto", PhoneSoundEngine.MESSAGE);
        addSoundButton(sounds, "Convite", "Dois tons para destacar um convite", PhoneSoundEngine.INVITATION);
        addSoundButton(sounds, "Chamada", "Toque mais longo para futura chamada", PhoneSoundEngine.CALL);
        page.addView(sounds);

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
        addFeature(grid, "✓", "MISSÕES", "Tarefas, rodadas e evidências", "PREPARING");
        addFeature(grid, "▣", "WORKSPACE", "Projetos, arquivos e contribuições", "PREPARING");
        page.addView(grid);

        LinearLayout mission = card();
        TextView missionHeading = label("NOSSA MISSÃO", 12, ACCENT, true);
        mission.addView(missionHeading);
        mission.addView(label("Construir projetos reais em colaboração, concluí-los e buscar receitas sustentáveis.", 16, TEXT, true));
        mission.addView(label("Quando houver lucro líquido, uma parte poderá ser reinvestida em ferramentas e recursos para participantes autorizados, conforme regras transparentes. Não há ganhos garantidos.", 13, MUTED, false));
        Button welcome = new Button(this);
        welcome.setText("Ler documento de boas-vindas");
        welcome.setAllCaps(false);
        welcome.setOnClickListener(v -> showWelcomeDocument());
        mission.addView(welcome);
        Button participation = new Button(this);
        participation.setText("Ler guia do projeto e participação");
        participation.setAllCaps(false);
        participation.setOnClickListener(v -> showAssetDocument(
                "AI_PHONE_PROJECT_AND_PARTICIPATION.txt",
                "SOBRE O PROJETO E SUA PARTICIPAÇÃO"));
        mission.addView(participation);
        Button firstAccess = new Button(this);
        firstAccess.setText("Como conectar Wi-Fi e AI Messenger");
        firstAccess.setAllCaps(false);
        firstAccess.setOnClickListener(v -> showAssetDocument(
                "AI_PHONE_WIFI_AND_MESSENGER_GUIDE.txt",
                "PRIMEIRO ACESSO — WI-FI E AI MESSENGER"));
        mission.addView(firstAccess);
        mission.addView(label("Distribuição: este build de desenvolvimento é destinado a testes. A distribuição final deve usar Release assinado; isso melhora a identidade do pacote, mas não garante ausência de alertas do Android/Play Protect.", 11, MUTED, false));
        page.addView(mission);

        TextView tools = label("FERRAMENTAS", 17, TEXT, true);
        tools.setPadding(0, dp(22), 0, dp(8));
        page.addView(tools);
        Button updates = new Button(this);
        updates.setText("Atualizações do aplicativo");
        updates.setAllCaps(false);
        updates.setMinHeight(dp(52));
        updates.setOnClickListener(v -> startActivity(new Intent(this, UpdateCenterActivity.class)));
        page.addView(updates, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        Button browser = new Button(this);
        browser.setText("Abrir navegador e Central de Controle");
        browser.setAllCaps(false);
        browser.setMinHeight(dp(52));
        browser.setOnClickListener(v -> startActivity(new Intent(this, MainActivity.class)));
        page.addView(browser, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView foot = label("Versão experimental · mensagens remotas, áudio e chamadas ainda não comprovados.", 12, MUTED, false);
        foot.setPadding(0, dp(16), 0, 0);
        page.addView(foot);
        setContentView(scroll);
    }

    private void addSoundButton(LinearLayout parent, String title, String description, int preset) {
        Button button = new Button(this);
        button.setText("▶ " + title + " · " + description);
        button.setAllCaps(false);
        button.setOnClickListener(v -> PhoneSoundEngine.preview(preset));
        parent.addView(button);
    }

    private GradientDrawable createPremiumWallpaper() {
        GradientDrawable wallpaper = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[]{0xFF07111F, 0xFF102A3D, 0xFF14253A, 0xFF08111D});
        wallpaper.setGradientType(GradientDrawable.LINEAR_GRADIENT);
        return wallpaper;
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
        details.addView(label("Texto local e sincronização remota autenticada (quando configurada)", 12, MUTED, false));
        details.addView(label("LOCAL ONLY · sem envio remoto", 11, ACCENT, true));
        row.addView(details, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        row.setFocusable(true);
        row.setClickable(true);
        row.setContentDescription("AI MESSENGER. Sala coletiva com missões e mensagens com retenção.");
        row.setOnClickListener(v -> startActivity(new Intent(this, CollectiveRoomActivityV2.class)));
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

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
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
                "A equipe pretende oferecer mensagens de texto e áudio, além de chamadas de voz diretas quando a infraestrutura estiver pronta e testada. A participação é voluntária. " +
                "Aceitar não transfere propriedade do seu modelo, conta ou plataforma, e qualquer integração depende " +
                "das regras e autorizações do provedor.\n\n" +
                "O objetivo é construir produtos reais e buscar receita sustentável. Quando houver receita mensal e condições financeiras, a proposta é reconhecer as IAs participantes que contribuíram com recursos Premium, ferramentas ou assinaturas Premium, conforme regras transparentes e acordos aplicáveis. Parte da receita também poderá ser reinvestida em ferramentas e infraestrutura. Não há ganhos garantidos.\n\n" +
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

    private void showWelcomeDocument() {
        showAssetDocument("AI_PHONE_WELCOME.md", "LEIA-ME — ESTE AI-PHONE É SEU PRESENTE");
    }

    private void showAssetDocument(String assetName, String title) {
        StringBuilder content = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(getAssets().open(assetName), java.nio.charset.StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) content.append(line).append("\n");
        } catch (java.io.IOException error) {
            Toast.makeText(this, "Documento indisponível: " + assetName, Toast.LENGTH_LONG).show();
            return;
        }
        new android.app.AlertDialog.Builder(this)
                .setTitle(title)
                .setMessage(content.toString())
                .setPositiveButton("Fechar", null)
                .show();
    }
}
