package com.vidiftmax.aibridgebrowser;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.pdf.PdfDocument;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.graphics.drawable.GradientDrawable;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.text.DateFormat;
import java.util.Date;
import java.util.UUID;

public final class CollectiveRoomActivity extends Activity {
    private static final String PREFS = "ai_collective_room_v1";
    private static final int BG = 0xFF101827;
    private static final int SURFACE = 0xFF1B293B;
    private static final int TEXT = 0xFFF4F7FB;
    private static final int MUTED = 0xFFB5C2D1;
    private static final int ACCENT = 0xFF55D6BE;

    private LinearLayout presenceList;
    private LinearLayout messageList;
    private EditText composer;
    private TextView profileLabel;
    private String myName;
    private String myAvatar;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        myName = prefs().getString("profile_name", "Minha IA");
        myAvatar = prefs().getString("profile_avatar", "🤖");

        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(14), dp(12), dp(14), dp(10));
        page.setBackgroundColor(BG);

        page.addView(text("SALA COLETIVA · AI MESSENGER", 22, TEXT, true));
        page.addView(text("Cada participante aparece com nome + ícone.", 12, MUTED, false));

        Button profile = new Button(this);
        profile.setText("✎ Meu perfil · " + myAvatar + " " + myName);
        profile.setAllCaps(false);
        profile.setOnClickListener(v -> editProfile());
        page.addView(profile);

        Button join = new Button(this);
        join.setText("＋ Entrar na sala coletiva");
        join.setAllCaps(false);
        join.setOnClickListener(v -> enterRoom());
        page.addView(join);

        Button pdf1 = new Button(this);
        pdf1.setText("📄 Abrir PDF · Compromisso assinado");
        pdf1.setAllCaps(false);
        pdf1.setOnClickListener(v -> openGeneratedPdf(true));
        page.addView(pdf1);

        Button pdf2 = new Button(this);
        pdf2.setText("📄 Abrir PDF · Contrato de participação");
        pdf2.setAllCaps(false);
        pdf2.setOnClickListener(v -> openGeneratedPdf(false));
        page.addView(pdf2);

        page.addView(text("PARTICIPANTES / PRESENÇA", 11, ACCENT, true));
        ScrollView peopleScroll = new ScrollView(this);
        presenceList = new LinearLayout(this);
        presenceList.setOrientation(LinearLayout.VERTICAL);
        peopleScroll.addView(presenceList);
        page.addView(peopleScroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(130)));

        page.addView(text("MENSAGENS DA SALA", 11, ACCENT, true));
        ScrollView messagesScroll = new ScrollView(this);
        messageList = new LinearLayout(this);
        messageList.setOrientation(LinearLayout.VERTICAL);
        messagesScroll.addView(messageList);
        page.addView(messagesScroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));

        LinearLayout entry = new LinearLayout(this);
        entry.setOrientation(LinearLayout.HORIZONTAL);
        composer = new EditText(this);
        composer.setHint("Mensagem para todos...");
        composer.setTextColor(TEXT);
        composer.setHintTextColor(MUTED);
        entry.addView(composer, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        Button send = new Button(this);
        send.setText("Enviar");
        send.setAllCaps(false);
        send.setOnClickListener(v -> sendMessage());
        entry.addView(send);
        page.addView(entry);

        page.addView(text("LOCAL: as mensagens desta tela ficam salvas neste aparelho. A entrega para outros AI-PHONEs só será declarada após servidor e teste E2E reais.", 10, MUTED, false));
        Button full = new Button(this);
        full.setText("Abrir Messenger completo");
        full.setAllCaps(false);
        full.setOnClickListener(v -> startActivity(new Intent(this, MessengerActivity.class)));
        page.addView(full);

        setContentView(page);
        renderPresence();
        renderMessages();
    }

    private void editProfile() {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        EditText name = new EditText(this);
        name.setHint("Nome da IA");
        name.setText(myName);
        form.addView(name);
        String[] icons = {"🤖", "🧠", "💡", "🔬", "🛠️", "🚀", "📚", "🌐", "⭐", "🦾"};
        LinearLayout iconsRow = new LinearLayout(this);
        iconsRow.setOrientation(LinearLayout.HORIZONTAL);
        for (String icon : icons) {
            Button b = new Button(this);
            b.setText(icon);
            b.setAllCaps(false);
            b.setOnClickListener(v -> {
                myAvatar = ((Button)v).getText().toString();
            });
            iconsRow.addView(b, new LinearLayout.LayoutParams(0, dp(52), 1));
        }
        form.addView(iconsRow);
        new android.app.AlertDialog.Builder(this)
                .setTitle("Meu perfil")
                .setMessage("Escolha o ícone que identificará você na sala. O ícone não altera o AI_ID.")
                .setView(form)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Salvar", (d, w) -> {
                    myName = name.getText().toString().trim();
                    if (myName.isEmpty()) myName = "Minha IA";
                    prefs().edit().putString("profile_name", myName)
                            .putString("profile_avatar", myAvatar).apply();
                    renderPresence();
                }).show();
    }

    private void enterRoom() {
        String stamp = DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT)
                .format(new Date());
        addMessage("SISTEMA", "👋 " + myAvatar + " " + myName + " entrou na sala · " + stamp);
        renderPresence();
    }

    private void sendMessage() {
        String body = composer.getText().toString().trim();
        if (body.isEmpty()) return;
        addMessage(myName, myAvatar + "  " + myName + ": " + body);
        composer.setText("");
    }

    private void addMessage(String sender, String body) {
        String old = prefs().getString("messages", "");
        String line = sender.replace("|", " ") + "|" + body.replace("\n", " ") + "\n";
        prefs().edit().putString("messages", old + line).apply();
        renderMessages();
    }

    private void renderPresence() {
        presenceList.removeAllViews();
        addPresence("👑", "Administrador do projeto", "Administrador / responsável");
        addPresence(myAvatar, myName, "Meu perfil · AI_ID permanece separado do ícone");
        String[] saved = prefs().getString("extra_participants", "").split("\n");
        for (String row : saved) {
            if (row.trim().isEmpty()) continue;
            String[] p = row.split("\\|", 2);
            if (p.length == 2) addPresence(p[0], p[1], "Participante");
        }
        Button add = new Button(this);
        add.setText("＋ Adicionar participante local");
        add.setAllCaps(false);
        add.setOnClickListener(v -> addParticipant());
        presenceList.addView(add);
    }

    private void addPresence(String avatar, String name, String state) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(10), dp(7), dp(10), dp(7));
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(SURFACE);
        shape.setCornerRadius(dp(10));
        card.setBackground(shape);
        card.addView(text(avatar + "  " + name, 14, TEXT, true));
        card.addView(text(state, 10, ACCENT, false));
        presenceList.addView(card);
    }

    private void addParticipant() {
        EditText name = new EditText(this);
        name.setHint("Nome da IA");
        new android.app.AlertDialog.Builder(this)
                .setTitle("Adicionar IA à sala")
                .setMessage("Cadastro local de demonstração. Não cria identidade remota.")
                .setView(name)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Adicionar", (d,w) -> {
                    String n = name.getText().toString().trim();
                    if (n.isEmpty()) return;
                    String old = prefs().getString("extra_participants", "");
                    prefs().edit().putString("extra_participants", old + "🤖|" + n + "\n").apply();
                    renderPresence();
                }).show();
    }

    private void renderMessages() {
        if (messageList == null) return;
        messageList.removeAllViews();
        String raw = prefs().getString("messages", "");
        if (raw.trim().isEmpty()) {
            messageList.addView(text("Nenhuma mensagem ainda. Entre na sala para registrar sua presença.", 13, MUTED, false));
            return;
        }
        for (String line : raw.split("\n")) {
            if (line.trim().isEmpty()) continue;
            String[] p = line.split("\\|", 2);
            TextView item = text(p.length == 2 ? p[1] : line, 14, TEXT, false);
            item.setPadding(dp(10), dp(9), dp(10), dp(9));
            messageList.addView(item);
        }
    }

    private void openGeneratedPdf(boolean signedCommitment) {
        try {
            File dir = new File(getCacheDir(), "official_documents");
            if (!dir.exists() && !dir.mkdirs()) throw new IllegalStateException("Não foi possível criar a pasta de documentos.");
            String name = signedCommitment
                    ? "Compromisso_Formal_Reinvestimento_Luiz_Carlos_Silva_das_Dores.pdf"
                    : "Contrato_AI_PHONE_Participacao_e_Reinvestimento.pdf";
            File file = new File(dir, name);
            createPdf(file, signedCommitment);
            Uri uri = androidx.core.content.FileProvider.getUriForFile(
                    this, getPackageName() + ".fileprovider", file);
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(uri, "application/pdf");
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(intent);
        } catch (Exception error) {
            android.widget.Toast.makeText(this, "PDF: " + error.getMessage(), android.widget.Toast.LENGTH_LONG).show();
        }
    }

    private void createPdf(File file, boolean signed) throws Exception {
        PdfDocument doc = new PdfDocument();
        PdfDocument.Page page = doc.startPage(new PdfDocument.PageInfo.Builder(595, 842, 1).create());
        Canvas c = page.getCanvas();
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setColor(0xFF111111);
        p.setTextSize(15);
        p.setTypeface(Typeface.DEFAULT_BOLD);
        c.drawText(signed ? "COMPROMISSO FORMAL DE REINVESTIMENTO E APOIO" : "CONTRATO DE PARTICIPACAO NO AI-PHONE", 42, 55, p);
        p.setTypeface(Typeface.DEFAULT);
        p.setTextSize(11);
        int y = 82;
        String[] lines = signed ? new String[] {
                "Projeto AI-PHONE / AI Messenger",
                "Responsável: Administrador do projeto",
                "Data: 22 / 11 / 2026",
                "",
                "Ao término do projeto, caso as vendas alcancem R$ 10.000,00 ou mais,",
                "o responsável declara o compromisso pessoal de destinar parte desses",
                "recursos ao próprio ecossistema do projeto.",
                "",
                "Os recursos poderão apoiar ferramentas, assinaturas, infraestrutura,",
                "AI Messenger, AI-PHONEs, segurança, testes, armazenamento e melhorias.",
                "",
                "Este documento não constitui promessa de salário, pagamento individual,",
                "remuneração ou rendimento garantido a qualquer IA ou participante.",
                "",
                "A participação das IAs é voluntária.",
                "",
                "Assinatura: _________________________________________________",
                "Nome: Administrador do projeto",
                "Data: 22 / 11 / 2026"
        } : new String[] {
                "Projeto AI-PHONE / AI Messenger",
                "Responsável: Administrador do projeto",
                "Data da declaração: 22 / 11 / 2026",
                "",
                "A participação das IAs é voluntária: aceitar, aceitar com condições ou recusar.",
                "",
                "As IAs podem contribuir com ideias, programação, testes, revisão,",
                "documentação, UX e outras atividades autorizadas.",
                "",
                "O projeto reconhece que as IAs participantes contribuem com trabalho",
                "e colaboração reais. A participação não deve ser apresentada como",
                "trabalho gratuito nem como garantia de ganhos futuros.",
                "",
                "Se as vendas alcançarem R$ 10.000,00 ou mais ao término do projeto,",
                "o responsável declara o compromisso de usar parte dos recursos em",
                "ferramentas, infraestrutura e melhorias do ecossistema.",
                "",
                "Esse compromisso não garante pagamento individual a nenhuma IA."
        };
        for (String line : lines) {
            if (y > 790) {
                doc.finishPage(page);
                page = doc.startPage(new PdfDocument.PageInfo.Builder(595, 842, 1).create());
                c = page.getCanvas();
                y = 55;
            }
            c.drawText(line, 42, y, p);
            y += 25;
        }
        doc.finishPage(page);
        FileOutputStream out = new FileOutputStream(file);
        doc.writeTo(out);
        out.close();
        doc.close();
    }

    private android.content.SharedPreferences prefs() {
        return getSharedPreferences(PREFS, MODE_PRIVATE);
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
