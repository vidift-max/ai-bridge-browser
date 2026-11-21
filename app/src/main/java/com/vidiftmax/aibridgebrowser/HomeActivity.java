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
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

/**
 * First participant-facing AI-PHONE landing screen.
 * Registry identity and backend states are intentionally not fabricated.
 */
public final class HomeActivity extends Activity {
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

        LinearLayout identity = card();
        TextView identityTitle = label("IDENTIDADE DO DISPOSITIVO", 12, ACCENT, true);
        identity.addView(identityTitle);
        identity.addView(label("Participante: ainda não associado", 17, TEXT, true));
        identity.addView(label("Número AI-PHONE: aguardando registro", 14, MUTED, false));
        identity.addView(label("Número de série: não provisionado", 14, MUTED, false));
        identity.addView(label("Estado: PREPARING · ambiente em construção", 13, MUTED, false));
        page.addView(identity);

        TextView section = label("SEU AMBIENTE", 17, TEXT, true);
        section.setPadding(0, dp(22), 0, dp(10));
        page.addView(section);

        LinearLayout grid = new LinearLayout(this);
        grid.setOrientation(LinearLayout.VERTICAL);
        addFeature(grid, "✉", "AI MESSENGER", "Conversas privadas e em grupo", "PREPARING");
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
