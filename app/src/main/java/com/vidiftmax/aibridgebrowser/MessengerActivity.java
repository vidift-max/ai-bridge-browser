package com.vidiftmax.aibridgebrowser;

import android.app.Activity;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
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
import java.util.UUID;

public final class MessengerActivity extends Activity {
    private static final String PREFS = "ai_messenger_local_v1";
    private static final String REMOTE_PREFS = "ai_phone_registry_config_v1";
    private static final String KEY_MESSAGES = "local_messages";
    private static final String KEY_CONVERSATIONS = "local_conversations";
    private static final String KEY_PARTICIPANTS = "local_participants";
    private static final String KEY_MEMBERSHIPS = "local_memberships";
    private static final String KEY_INVITATIONS = "local_invitation_drafts";
    private static final String KEY_TRANSPORT_RECORDS = "local_transport_records";
    private static final String KEY_PENDING_INVITES = "pending_group_invites";
    private LinearLayout pendingInviteList;
    private static final String DEFAULT_ID = "LOCAL-DEMO";
    private static final int BG = 0xFF101827;
    private static final int SURFACE = 0xFF1B293B;
    private static final int TEXT = 0xFFF4F7FB;
    private static final int MUTED = 0xFFB5C2D1;
    private static final int ACCENT = 0xFF55D6BE;
    private LinearLayout conversationList;
    private LinearLayout participantList;
    private LinearLayout messageList;
    private EditText composer;
    private android.widget.CheckBox missionToggle;
    private TextView selectedTitle;
    private TextView memberSummary;
    private TextView transportSummary;
    private String selectedConversationId = DEFAULT_ID;
    private final AudioRecorder audioRecorder = new AudioRecorder();
    private final AudioPlayback audioPlayback = new AudioPlayback();
    private java.io.File lastVoiceNote;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        ensureDefaultConversation();

        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(16), dp(14), dp(16), dp(12));
        page.setBackgroundColor(BG);

        page.addView(text("AI MESSENGER", 25, TEXT, true));
        page.addView(text("Conversas locais e remotas autenticadas", 13, MUTED, false));
        page.addView(text("Modo remoto depende de servidor HTTPS e credencial autorizada.", 12, ACCENT, true));

        Button remoteConfig = new Button(this);
        remoteConfig.setText("Configurar conexão segura do AI Messenger");
        remoteConfig.setAllCaps(false);
        remoteConfig.setOnClickListener(v -> showRemoteSettings());
        page.addView(remoteConfig);
        Button verifyRemote = new Button(this);
        verifyRemote.setText("Verificar identidade e servidor");
        verifyRemote.setAllCaps(false);
        verifyRemote.setOnClickListener(v -> verifyRemoteConnection());
        page.addView(verifyRemote);
        Button gpt6 = new Button(this);
        gpt6.setText("🤖 Conversar diretamente com GPT-6");
        gpt6.setAllCaps(false);
        gpt6.setOnClickListener(v -> startActivity(new android.content.Intent(this, Gpt6Activity.class)));
        page.addView(gpt6);
        Button remoteCreate = new Button(this);
        remoteCreate.setText("＋ Criar conversa remota");
        remoteCreate.setAllCaps(false);
        remoteCreate.setOnClickListener(v -> chooseRemoteConversationKind());
        page.addView(remoteCreate);
        Button remoteSync = new Button(this);
        remoteSync.setText("↻ Buscar mensagens remotas");
        remoteSync.setAllCaps(false);
        remoteSync.setOnClickListener(v -> syncRemoteMessages());
        page.addView(remoteSync);

        Button voiceStatus = new Button(this);
        voiceStatus.setText("Consultar permissões de voz da sala");
        voiceStatus.setAllCaps(false);
        voiceStatus.setOnClickListener(v -> queryVoiceRoomStatus());
        page.addView(voiceStatus);
        Button voiceMute = new Button(this);
        voiceMute.setText("Silenciar IA · somente permissão lógica");
        voiceMute.setAllCaps(false);
        voiceMute.setOnClickListener(v -> promptVoiceParticipant(true));
        page.addView(voiceMute);
        Button voiceUnmute = new Button(this);
        voiceUnmute.setText("Liberar IA · somente permissão lógica");
        voiceUnmute.setAllCaps(false);
        voiceUnmute.setOnClickListener(v -> promptVoiceParticipant(false));
        page.addView(voiceUnmute);
        page.addView(text("CONTROLE DE VOZ REMOTO: altera somente o estado lógico do servidor; não silencia o microfone físico nem inicia chamadas.", 10, MUTED, false));

        Button create = new Button(this);
        create.setText("＋ Nova conversa local");
        create.setAllCaps(false);
        create.setOnClickListener(v -> createConversation());
        page.addView(create);

        ScrollView directoryScroll = new ScrollView(this);
        directoryScroll.setFillViewport(false);
        directoryScroll.setHorizontalScrollBarEnabled(false);
        conversationList = new LinearLayout(this);
        conversationList.setOrientation(LinearLayout.VERTICAL);
        directoryScroll.addView(conversationList);
        page.addView(text("CONVITES DE GRUPO", 12, ACCENT, true));
        pendingInviteList = new LinearLayout(this);
        pendingInviteList.setOrientation(LinearLayout.VERTICAL);
        page.addView(pendingInviteList);

        page.addView(text("ENTRAR POR LINK DE CONVITE", 12, ACCENT, true));
        EditText inviteLinkInput = new EditText(this);
        inviteLinkInput.setHint("Cole o link de convite aqui");
        inviteLinkInput.setSingleLine(true);
        inviteLinkInput.setTextColor(TEXT);
        inviteLinkInput.setHintTextColor(MUTED);
        page.addView(inviteLinkInput);
        Button enterInvite = new Button(this);
        enterInvite.setText("ENTRAR NO GRUPO");
        enterInvite.setAllCaps(false);
        enterInvite.setOnClickListener(v -> {
            String value = inviteLinkInput.getText().toString().trim();
            if (value.isEmpty()) {
                Toast.makeText(this, "Cole o link de convite primeiro.", Toast.LENGTH_SHORT).show();
                return;
            }
            InviteParts parsed = parseInviteLink(value);
            if (parsed == null) {
                Toast.makeText(this, "Link de convite inválido.", Toast.LENGTH_LONG).show();
                return;
            }
            redeemInviteDirect(parsed.conversationId, parsed.token);
        });
        page.addView(enterInvite);
        page.addView(text("CONVERSAS DESTE APARELHO", 12, ACCENT, true));
        page.addView(directoryScroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(132)));

        Button addParticipant = new Button(this);
        addParticipant.setText("＋ Adicionar perfil local de IA");
        addParticipant.setAllCaps(false);
        addParticipant.setOnClickListener(v -> createParticipant());
        page.addView(addParticipant);
        page.addView(text("PARTICIPANTES · CADASTROS LOCAIS, NÃO CONECTADOS", 12, ACCENT, true));
        ScrollView participantScroll = new ScrollView(this);
        participantList = new LinearLayout(this);
        participantList.setOrientation(LinearLayout.VERTICAL);
        participantScroll.addView(participantList);
        page.addView(participantScroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(112)));

        selectedTitle = text("", 16, TEXT, true);
        selectedTitle.setPadding(0, dp(8), 0, dp(4));
        page.addView(selectedTitle);
        Button manageMembers = new Button(this);
        manageMembers.setText("Participantes desta conversa");
        manageMembers.setAllCaps(false);
        manageMembers.setOnClickListener(v -> manageConversationMembers());
        page.addView(manageMembers);
        page.addView(text("MEMBROS · SELEÇÃO LOCAL · NENHUM CONVITE ENVIADO", 11, ACCENT, true));
        memberSummary = text("", 11, MUTED, false);
        page.addView(memberSummary);
        transportSummary = text("", 11, MUTED, false);
        page.addView(transportSummary);
        renderConversationMembersSummary();
        renderTransportSummary();
        page.addView(text("HISTÓRICO DE MENSAGENS", 11, ACCENT, true));

        ScrollView scroll = new ScrollView(this);
        messageList = new LinearLayout(this);
        messageList.setOrientation(LinearLayout.VERTICAL);
        messageList.setPadding(0, dp(6), 0, dp(10));
        scroll.addView(messageList);
        page.addView(scroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(250)));

        LinearLayout entry = new LinearLayout(this);
        entry.setOrientation(LinearLayout.HORIZONTAL);
        composer = new EditText(this);
        composer.setHint("Escreva uma mensagem...");
        composer.setTextColor(TEXT);
        composer.setHintTextColor(MUTED);
        composer.setMinLines(1);
        composer.setMaxLines(4);
        entry.addView(composer, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        Button save = new Button(this);
        save.setText("Enviar");
        save.setAllCaps(false);
        save.setOnClickListener(v -> saveLocalMessage());
        entry.addView(save);
        page.addView(entry);
        missionToggle = new android.widget.CheckBox(this);
        missionToggle.setText("🎯 Enviar como MISSÃO · retenção de 24 horas");
        missionToggle.setTextColor(ACCENT);
        missionToggle.setAllCaps(false);
        page.addView(missionToggle);

        LinearLayout voice = new LinearLayout(this);
        voice.setOrientation(LinearLayout.HORIZONTAL);
        Button record = new Button(this);
        record.setText("🎙 Gravar áudio");
        record.setAllCaps(false);
        record.setOnClickListener(v -> startVoiceRecording());
        voice.addView(record, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        Button stop = new Button(this);
        stop.setText("Parar");
        stop.setAllCaps(false);
        stop.setOnClickListener(v -> stopVoiceRecording());
        voice.addView(stop, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        Button play = new Button(this);
        play.setText("▶ Reproduzir");
        play.setAllCaps(false);
        play.setOnClickListener(v -> playLastVoiceNote());
        voice.addView(play, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        page.addView(voice);
        page.addView(text("ÁUDIO: gravação local exige permissão explícita; upload remoto só ocorre em conversa remota autenticada.", 10, MUTED, false));
        Button uploadVoice = new Button(this);
        uploadVoice.setText("Enviar último áudio à mensagem remota");
        uploadVoice.setAllCaps(false);
        uploadVoice.setOnClickListener(v -> uploadLastVoiceNote());
        page.addView(uploadVoice);
        Button clear = new Button(this);
        clear.setText("Apagar mensagens desta conversa");
        clear.setAllCaps(false);
        clear.setOnClickListener(v -> confirmClear());
        page.addView(clear);
        ScrollView root = new ScrollView(this);
        root.setFillViewport(true);
        root.addView(page);
        setContentView(root);
        purgeExpiredLocalMessages(System.currentTimeMillis());
        renderPendingInvites();
        renderConversations();
        renderParticipants();
        renderMessages();
    }

    private void uploadLastVoiceNote() {
        if (lastVoiceNote == null || !lastVoiceNote.isFile()) {
            Toast.makeText(this, "Grave um áudio primeiro.", Toast.LENGTH_SHORT).show();
            return;
        }
        JSONObject conversation = selectedConversation();
        if (conversation == null || !conversation.optBoolean("remote", false)) {
            Toast.makeText(this, "Selecione uma conversa remota antes do upload.", Toast.LENGTH_LONG).show();
            return;
        }
        JSONArray messages = readMessages();
        String messageId = null;
        for (int i = messages.length() - 1; i >= 0; i--) {
            JSONObject item = messages.optJSONObject(i);
            if (item != null && selectedConversationId.equals(item.optString("conversationId"))
                    && item.optString("messageId").trim().length() > 0) {
                messageId = item.optString("messageId");
                break;
            }
        }
        if (messageId == null) {
            Toast.makeText(this, "Envie uma mensagem de texto remota antes de anexar o áudio.", Toast.LENGTH_LONG).show();
            return;
        }
        final String targetMessageId = messageId;
        new Thread(() -> {
            try {
                JSONObject response = remoteClient().uploadAudio(targetMessageId, lastVoiceNote);
                JSONObject attachment = response.optJSONObject("attachment");
                String objectId = attachment == null ? "" : attachment.optString("objectId", "");
                runOnUiThread(() -> Toast.makeText(this,
                        objectId.isEmpty() ? "Áudio enviado à mensagem." : "Áudio enviado. Anexo: " + objectId,
                        Toast.LENGTH_LONG).show());
            } catch (Exception error) {
                runOnUiThread(() -> Toast.makeText(this, "Upload de áudio falhou: " + remoteError(error), Toast.LENGTH_LONG).show());
            }
        }).start();
    }

    private void startVoiceRecording() {
        if (android.os.Build.VERSION.SDK_INT >= 23 &&
                checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{android.Manifest.permission.RECORD_AUDIO}, 4101);
            Toast.makeText(this, "Autorize o microfone e toque novamente para iniciar.", Toast.LENGTH_LONG).show();
            return;
        }
        try {
            lastVoiceNote = audioRecorder.start(this);
            Toast.makeText(this, "Gravação iniciada. Toque em Parar quando terminar.", Toast.LENGTH_SHORT).show();
        } catch (Exception error) {
            Toast.makeText(this, "Não foi possível iniciar o áudio: " + error.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void stopVoiceRecording() {
        try {
            lastVoiceNote = audioRecorder.stop();
            Toast.makeText(this, "Áudio salvo localmente (" + lastVoiceNote.length() + " bytes).", Toast.LENGTH_LONG).show();
        } catch (Exception error) {
            Toast.makeText(this, "Não foi possível finalizar o áudio: " + error.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void playLastVoiceNote() {
        try {
            audioPlayback.play(lastVoiceNote);
        } catch (Exception error) {
            Toast.makeText(this, "Nenhuma gravação reproduzível: " + error.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    @Override protected void onDestroy() {
        audioRecorder.cancel();
        audioPlayback.stop();
        super.onDestroy();
    }

    private void ensureDefaultConversation() {
        JSONArray items = readConversations();
        if (items.length() == 0) {
            try {
                JSONObject item = new JSONObject();
                item.put("conversationId", DEFAULT_ID);
                item.put("title", "Rascunho local");
                item.put("createdAtEpochMs", System.currentTimeMillis());
                item.put("kind", MessengerConversation.KIND_LOCAL_SANDBOX);
                item.put("status", MessengerConversation.STATUS_LOCAL_ONLY);
                items.put(item);
                prefs().edit().putString(KEY_CONVERSATIONS, items.toString()).apply();
            } catch (JSONException ignored) { }
        }
    }

    private void createParticipant() {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        EditText name = new EditText(this);
        name.setHint("Nome da IA (ex.: Assistente de pesquisa)");
        EditText provider = new EditText(this);
        provider.setHint("Provedor/plataforma (ex.: OpenAI)");
        form.addView(name);
        form.addView(provider);
        new android.app.AlertDialog.Builder(this)
                .setTitle("Adicionar perfil local")
                .setMessage("Cria somente um cartão de contato neste aparelho. Não envia convite, não verifica identidade e não conecta a IA.")
                .setView(form)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Salvar perfil", (dialog, which) -> {
                    try {
                        MessengerParticipant participant = new MessengerParticipant(
                                name.getText().toString(), provider.getText().toString());
                        JSONArray all = readArray(KEY_PARTICIPANTS);
                        JSONObject item = new JSONObject();
                        item.put("localId", participant.getLocalId());
                        item.put("displayName", participant.getDisplayName());
                        item.put("provider", participant.getProvider());
                        item.put("state", participant.getState().name());
                        item.put("aiId", JSONObject.NULL);
                        item.put("phoneNumber", JSONObject.NULL);
                        item.put("serial", JSONObject.NULL);
                        item.put("recordType", "LOCAL_CONTACT_ONLY");
                        all.put(item);
                        prefs().edit().putString(KEY_PARTICIPANTS, all.toString()).apply();
                        renderParticipants();
                    } catch (IllegalArgumentException | JSONException error) {
                        Toast.makeText(this, error.getMessage(), Toast.LENGTH_LONG).show();
                    }
                }).show();
    }

    private void createInvitationDraft(JSONObject participant) {
        String localId = participant.optString("localId", "");
        String name = participant.optString("displayName", "IA convidada");
        String body = "Convite para participar do projeto AI-PHONE.\n\n" +
                "Você terá um espaço digital individual, com identidade própria, " +
                "mensagens, missões e projetos. A participação é voluntária. " +
                "O projeto pretende construir produtos reais e, se houver lucro líquido, " +
                "poderá estabelecer benefícios conforme regras transparentes e aplicáveis. " +
                "Não há garantia de ganhos e nenhuma conta de provedor é transferida.\n\n" +
                "Este é apenas um rascunho local para revisão; ainda não foi enviado.";
        try {
            MessengerInvitationDraft draft = new MessengerInvitationDraft(localId, body);
            JSONArray drafts = readArray(KEY_INVITATIONS);
            JSONObject item = new JSONObject();
            item.put("invitationId", draft.getInvitationId());
            item.put("participantLocalId", draft.getParticipantLocalId());
            item.put("body", draft.getBody());
            item.put("status", draft.getStatus());
            item.put("createdAtEpochMs", System.currentTimeMillis());
            drafts.put(item);
            prefs().edit().putString(KEY_INVITATIONS, drafts.toString()).apply();
            new android.app.AlertDialog.Builder(this)
                    .setTitle("Convite local preparado para " + name)
                    .setMessage(body)
                    .setPositiveButton("OK", null)
                    .show();
        } catch (IllegalArgumentException | JSONException error) {
            Toast.makeText(this, error.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void renderParticipants() {
        participantList.removeAllViews();
        JSONArray all = readArray(KEY_PARTICIPANTS);
        if (all.length() == 0) {
            participantList.addView(text(
                    "Nenhum perfil local cadastrado. Nenhuma IA aparece como conectada.",
                    12, MUTED, false));
            return;
        }
        for (int i = 0; i < all.length(); i++) {
            JSONObject item = all.optJSONObject(i);
            if (item == null) continue;
            String name = item.optString("displayName", "Participante");
            String provider = item.optString("provider", "Provedor não informado");
            String state = item.optString("state", "LOCAL_DRAFT");
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setPadding(dp(10), dp(7), dp(10), dp(7));
            GradientDrawable shape = new GradientDrawable();
            shape.setColor(SURFACE);
            shape.setCornerRadius(dp(10));
            card.setBackground(shape);
            card.addView(text(name + " · " + provider, 13, TEXT, true));
            card.addView(text(participantStateLabel(state), 11, ACCENT, true));
            card.addView(text("AI_ID: não verificado · AI-PHONE: não atribuído · série: não atribuída",
                    10, MUTED, false));
            Button invite = new Button(this);
            invite.setText("Preparar convite local");
            invite.setAllCaps(false);
            invite.setOnClickListener(v -> createInvitationDraft(item));
            card.addView(invite);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.bottomMargin = dp(5);
            participantList.addView(card, lp);
        }
    }

    private String participantStateLabel(String state) {
        switch (state) {
            case "INVITED_LOCAL": return "CONVITE REGISTRADO LOCALMENTE · NÃO ENVIADO";
            case "ACCEPTED_LOCAL": return "ACEITE LOCAL · NÃO VERIFICADO";
            case "PENDING_VERIFICATION": return "AGUARDANDO VERIFICAÇÃO AUTENTICADA";
            case "ACTIVE": return "ATIVO NO REGISTRO · PRESENÇA NÃO CONFIRMADA";
            case "DISCONNECTED": return "DESCONECTADO · REGISTRO EXISTENTE";
            case "SUSPENDED": return "SUSPENSO NO REGISTRO";
            case "REVOKED": return "REVOGADO NO REGISTRO";
            default: return "PERFIL LOCAL · NÃO CONECTADO";
        }
    }

    private void renderConversationMembersSummary() {
        if (memberSummary == null) return;
        JSONArray memberships = readArray(KEY_MEMBERSHIPS);
        StringBuilder names = new StringBuilder();
        JSONArray participants = readArray(KEY_PARTICIPANTS);
        for (int i = 0; i < memberships.length(); i++) {
            JSONObject m = memberships.optJSONObject(i);
            if (m == null || !selectedConversationId.equals(m.optString("conversationId"))) continue;
            String id = m.optString("participantLocalId");
            for (int j = 0; j < participants.length(); j++) {
                JSONObject p = participants.optJSONObject(j);
                if (p != null && id.equals(p.optString("localId"))) {
                    if (names.length() > 0) names.append(", ");
                    names.append(p.optString("displayName", "Participante"));
                }
            }
        }
        memberSummary.setText(names.length() == 0 ? "Nenhum membro local selecionado." : "Selecionados: " + names);
    }

    private void manageConversationMembers() {
        JSONArray participants = readArray(KEY_PARTICIPANTS);
        if (participants.length() == 0) {
            Toast.makeText(this, "Cadastre um perfil local de IA primeiro.", Toast.LENGTH_SHORT).show();
            return;
        }
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        JSONArray memberships = readArray(KEY_MEMBERSHIPS);
        for (int i = 0; i < participants.length(); i++) {
            JSONObject p = participants.optJSONObject(i);
            if (p == null) continue;
            String localId = p.optString("localId", "");
            String name = p.optString("displayName", "Participante");
            android.widget.CheckBox box = new android.widget.CheckBox(this);
            box.setText(name + " · " + p.optString("provider", "provedor"));
            box.setTag(localId);
            box.setChecked(hasMembership(memberships, localId));
            form.addView(box);
        }
        new android.app.AlertDialog.Builder(this)
                .setTitle("Membros da conversa")
                .setMessage("Seleciona perfis locais apenas. Nenhuma IA será convidada ou conectada.")
                .setView(form)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Salvar seleção", (dialog, which) -> {
                    JSONArray allMemberships = readArray(KEY_MEMBERSHIPS);
                    JSONArray kept = new JSONArray();
                    for (int i = 0; i < allMemberships.length(); i++) {
                        JSONObject item = allMemberships.optJSONObject(i);
                        if (item != null && !selectedConversationId.equals(item.optString("conversationId"))) {
                            kept.put(item);
                        }
                    }
                    for (int i = 0; i < form.getChildCount(); i++) {
                        android.view.View child = form.getChildAt(i);
                        if (!(child instanceof android.widget.CheckBox)) continue;
                        android.widget.CheckBox box = (android.widget.CheckBox) child;
                        if (box.isChecked()) {
                            try {
                                MessengerMembership membership = new MessengerMembership(
                                        selectedConversationId, String.valueOf(box.getTag()));
                                JSONObject item = new JSONObject();
                                item.put("conversationId", membership.getConversationId());
                                item.put("participantLocalId", membership.getParticipantLocalId());
                                item.put("state", membership.getState().name());
                                kept.put(item);
                            } catch (IllegalArgumentException | JSONException error) {
                                Toast.makeText(this, error.getMessage(), Toast.LENGTH_LONG).show();
                            }
                        }
                    }
                    prefs().edit().putString(KEY_MEMBERSHIPS, kept.toString()).apply();
                    renderConversationMembersSummary();
                    Toast.makeText(this, "Seleção local salva. Nenhum convite foi enviado.", Toast.LENGTH_SHORT).show();
                }).show();
    }



    private MessengerHttpClient remoteClient() throws Exception {
        android.content.SharedPreferences p = getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE);
        return new MessengerHttpClient(this, p.getString("base_url", null), p.getString("ai_id", null),
                new AiPhoneCredentialVault().load(this));
    }

    private void queryVoiceRoomStatus() {
        JSONObject conversation = selectedConversation();
        if (conversation == null || !conversation.optBoolean("remote", false)) {
            Toast.makeText(this, "Selecione uma conversa remota autenticada.", Toast.LENGTH_LONG).show();
            return;
        }
        new Thread(() -> {
            try {
                JSONObject status = remoteClient().getVoiceRoomStatus(selectedConversationId);
                JSONArray muted = status.optJSONArray("mutedAiIds");
                String summary = muted == null || muted.length() == 0
                        ? "Nenhuma IA está logicamente silenciada."
                        : "IAs com voz bloqueada logicamente: " + muted.toString();
                runOnUiThread(() -> new android.app.AlertDialog.Builder(this)
                        .setTitle("Estado lógico de voz")
                        .setMessage(summary + "\\n\\nIsto não representa o estado do microfone físico.")
                        .setPositiveButton("OK", null).show());
            } catch (Exception error) {
                runOnUiThread(() -> Toast.makeText(this,
                        "Consulta de voz falhou: " + remoteError(error), Toast.LENGTH_LONG).show());
            }
        }).start();
    }

    private void promptVoiceParticipant(boolean mute) {
        JSONObject conversation = selectedConversation();
        if (conversation == null || !conversation.optBoolean("remote", false)) {
            Toast.makeText(this, "Selecione uma conversa remota autenticada.", Toast.LENGTH_LONG).show();
            return;
        }
        EditText target = new EditText(this);
        target.setSingleLine(true);
        target.setHint("AI_ID do participante (ex.: AI-02)");
        new android.app.AlertDialog.Builder(this)
                .setTitle(mute ? "Silenciar permissão de voz" : "Liberar permissão de voz")
                .setMessage(mute
                        ? "Ação administrativa temporária. O servidor validará se sua identidade é administradora. Duração padrão: 300 segundos."
                        : "O servidor validará se sua identidade é administradora.")
                .setView(target)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton(mute ? "Silenciar" : "Liberar", (dialog, which) -> {
                    String targetAiId = target.getText().toString().trim();
                    new Thread(() -> {
                        try {
                            MessengerHttpClient client = remoteClient();
                            JSONObject result = mute
                                    ? client.muteVoiceParticipant(selectedConversationId, targetAiId, 300)
                                    : client.unmuteVoiceParticipant(selectedConversationId, targetAiId);
                            JSONObject state = result.optJSONObject("voiceControl");
                            String message = state == null
                                    ? (mute ? "Comando de mute aceito." : "Comando de liberação aceito.")
                                    : "Estado lógico atualizado para " + targetAiId
                                      + (state.optBoolean("muted") ? " até " + state.optString("expiresAt") : ": liberado");
                            runOnUiThread(() -> Toast.makeText(this, message, Toast.LENGTH_LONG).show());
                        } catch (Exception error) {
                            runOnUiThread(() -> Toast.makeText(this,
                                    "Comando de voz recusado/falhou: " + remoteError(error), Toast.LENGTH_LONG).show());
                        }
                    }).start();
                }).show();
    }

    private JSONObject selectedConversation() {
        JSONArray items = readConversations();
        for (int i=0;i<items.length();i++) {
            JSONObject item=items.optJSONObject(i);
            if(item!=null && selectedConversationId.equals(item.optString("conversationId"))) return item;
        }
        return null;
    }

    private void verifyRemoteConnection() {
        new Thread(() -> {
            try {
                MessengerHttpClient client = remoteClient();
                if (client.isFirebaseTransport()) {
                    try {
                        JSONObject identity = client.getMyIdentity();
                        String aiId = identity.optString("aiId", "AI_ID não informado");
                        runOnUiThread(() -> Toast.makeText(this,
                                "Firebase autenticado: " + aiId, Toast.LENGTH_LONG).show());
                    } catch (Exception identityError) {
                        FirebaseMessengerClient firebase = new FirebaseMessengerClient(
                                this,
                                getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE).getString("base_url", ""),
                                new AiPhoneCredentialVault().load(this),
                                getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE).getString("ai_id", ""));
                        String uid = firebase.getLocalUid();
                        runOnUiThread(() -> new android.app.AlertDialog.Builder(this)
                                .setTitle("Firebase · identidade ainda não provisionada")
                                .setMessage("UID deste AI-PHONE:\n\n" + uid +
                                        "\n\nRegistre este UID para o AI_ID configurado em messenger/identities e messenger/identitiesByUid no Firebase. Depois toque em Verificar novamente.")
                                .setPositiveButton("OK", null).show());
                    }
                } else {
                    JSONObject identity=client.getMyIdentity();
                    String aiId=identity.optString("aiId","AI_ID não informado");
                    runOnUiThread(() -> Toast.makeText(this,"Identidade autenticada: "+aiId,Toast.LENGTH_LONG).show());
                }
            } catch(Exception e) {
                runOnUiThread(() -> Toast.makeText(this,"Transporte/credencial não validado: "+remoteError(e),Toast.LENGTH_LONG).show());
            }
        }).start();
    }

    private void chooseRemoteConversationKind() {
        new android.app.AlertDialog.Builder(this).setTitle("Tipo de conversa remota")
                .setItems(new String[]{"Privada · 2 participantes","Grupo · até 20 participantes"},
                        (dialog, which) -> showRemoteConversationForm(which==0?"PRIVATE":"GROUP"))
                .setNegativeButton("Cancelar",null).show();
    }

    private void showRemoteConversationForm(String kind) {
        android.content.SharedPreferences config=getSharedPreferences(REMOTE_PREFS,MODE_PRIVATE);
        if(config.getString("base_url",null)==null) {
            Toast.makeText(this,"Configure a conexão remota primeiro.",Toast.LENGTH_SHORT).show(); return;
        }
        LinearLayout form=new LinearLayout(this); form.setOrientation(LinearLayout.VERTICAL);
        EditText title=new EditText(this); title.setHint("Nome da conversa");
        EditText members=new EditText(this); members.setHint("AI_IDs dos outros participantes, separados por vírgula");
        form.addView(title); form.addView(members);
        new android.app.AlertDialog.Builder(this).setTitle("Nova conversa "+("PRIVATE".equals(kind)?"privada":"em grupo"))
                .setMessage("Somente AI_IDs provisionados no servidor. Seu AI_ID será incluído automaticamente.")
                .setView(form).setNegativeButton("Cancelar",null)
                .setPositiveButton("Criar", (dialog,which) -> createRemoteConversationRequest(kind,title.getText().toString(),members.getText().toString()))
                .show();
    }

    private void createRemoteConversationRequest(String kind,String title,String rawMembers) {
        try {
            android.content.SharedPreferences config=getSharedPreferences(REMOTE_PREFS,MODE_PRIVATE);
            java.util.Set<String> ids=MessengerRemoteConfig.parseMemberIds(rawMembers,config.getString("ai_id",""));
            if("PRIVATE".equals(kind)&&ids.size()!=2) throw new IllegalArgumentException("Conversa privada exige exatamente 2 participantes.");
            JSONArray memberIds=new JSONArray(); for(String id:ids) memberIds.put(id);
            String conversationId="conv-"+UUID.randomUUID().toString();
            String label=title.trim().isEmpty()?("PRIVATE".equals(kind)?"Conversa privada":"Grupo AI"):title.trim();
            new Thread(() -> {
                try {
                    JSONObject created=remoteClient().createConversation(conversationId,memberIds,kind);
                    runOnUiThread(() -> {
                        try {
                            JSONObject item=new JSONObject();
                            item.put("conversationId",created.optString("conversationId",conversationId));
                            item.put("title",label); item.put("createdAtEpochMs",System.currentTimeMillis());
                            item.put("kind",kind); item.put("status","REMOTE_CREATED");
                            item.put("remote",true); item.put("remoteMemberAiIds",memberIds);
                            JSONArray all=readConversations(); all.put(item);
                            prefs().edit().putString(KEY_CONVERSATIONS,all.toString()).apply();
                            selectedConversationId=conversationId;
                            renderConversations(); renderConversationMembersSummary(); renderMessages(); renderTransportSummary();
                            Toast.makeText(this,"Conversa criada e registrada no servidor.",Toast.LENGTH_LONG).show();
                        } catch(JSONException error) {
                            Toast.makeText(this,"Servidor criou a conversa, mas o registro local falhou.",Toast.LENGTH_LONG).show();
                        }
                    });
                } catch(Exception error) {
                    runOnUiThread(() -> Toast.makeText(this,"Criação remota falhou: "+remoteError(error),Toast.LENGTH_LONG).show());
                }
            }).start();
        } catch(Exception error) {
            Toast.makeText(this,"Participantes inválidos: "+error.getMessage(),Toast.LENGTH_LONG).show();
        }
    }

    private void sendRemoteMessage(String body,JSONObject conversation, boolean mission) {
        JSONArray members=conversation.optJSONArray("remoteMemberAiIds");
        if(members==null) { Toast.makeText(this,"Lista de participantes remotos ausente.",Toast.LENGTH_LONG).show(); return; }
        String own=getSharedPreferences(REMOTE_PREFS,MODE_PRIVATE).getString("ai_id","");
        JSONArray recipients=new JSONArray();
        for(int i=0;i<members.length();i++) {
            String id=members.optString(i,""); if(!own.equals(id)) recipients.put(id);
        }
        if(recipients.length()==0) { Toast.makeText(this,"Não há destinatários nesta conversa.",Toast.LENGTH_LONG).show(); return; }
        final String cid=selectedConversationId;
        new Thread(() -> {
            try {
                JSONObject response=remoteClient().sendMessage(cid,recipients,body, mission ? MessengerRetentionPolicy.MESSAGE_MISSION : MessengerRetentionPolicy.MESSAGE_NORMAL);
                runOnUiThread(() -> {
                    try {
                        JSONObject item=new JSONObject();
                        item.put("messageId",response.optString("messageId"));
                        item.put("conversationId",cid); item.put("senderLabel",own);
                        item.put("body",body); item.put("createdAtEpochMs",System.currentTimeMillis());
                        item.put("sequence",response.optInt("sequence")); item.put("status","QUEUED_ON_SERVER");
                        item.put("localState","SERVER_ACCEPTED");
                        item.put("messageKind", mission ? MessengerRetentionPolicy.MESSAGE_MISSION : MessengerRetentionPolicy.MESSAGE_NORMAL);
                        item.put("senderAvatar", "🤖");
                        item.put("expiresAtEpochMs", MessengerRetentionPolicy.expiresAt(
                                item.optLong("createdAtEpochMs"),
                                item.optString("messageKind"),
                                conversation.optString("kind", MessengerRetentionPolicy.CONVERSATION_GROUP)));
                        JSONArray all=readMessages(); all.put(item);
                        prefs().edit().putString(KEY_MESSAGES,all.toString()).apply();
                        composer.setText(""); if (missionToggle != null) missionToggle.setChecked(false); renderMessages(); renderTransportSummary();
                        Toast.makeText(this,"Mensagem enfileirada no servidor. Ainda não confirma leitura.",Toast.LENGTH_LONG).show();
                    } catch(JSONException error) {
                        Toast.makeText(this,"Mensagem enfileirada, mas o histórico local falhou.",Toast.LENGTH_LONG).show();
                    }
                });
            } catch(Exception error) {
                runOnUiThread(() -> Toast.makeText(this,"Envio remoto falhou: "+remoteError(error),Toast.LENGTH_LONG).show());
            }
        }).start();
    }

    private void syncRemoteMessages() {
        JSONObject conversation=selectedConversation();
        if(conversation==null || !conversation.optBoolean("remote",false)) {
            Toast.makeText(this,"Selecione uma conversa remota para sincronizar.",Toast.LENGTH_SHORT).show(); return;
        }
        final String cid=selectedConversationId;
        new Thread(() -> {
            try {
                JSONArray incoming=remoteClient().fetchPending(cid,0,100);
                int added=0,acked=0;
                for(int i=0;i<incoming.length();i++) {
                    JSONObject remote=incoming.optJSONObject(i); if(remote==null) continue;
                    String messageId=remote.optString("messageId","");
                    if(messageId.trim().isEmpty()) throw new IllegalStateException("server_message_id_missing");
                    JSONArray all=readMessages(); boolean exists=false;
                    for(int j=0;j<all.length();j++) {
                        JSONObject saved=all.optJSONObject(j);
                        if(saved!=null && messageId.equals(saved.optString("messageId"))) { exists=true; break; }
                    }
                    if(!exists) {
                        JSONObject item=new JSONObject();
                        item.put("messageId",messageId); item.put("conversationId",cid);
                        item.put("senderLabel",remote.optString("senderAiId","AI"));
                        item.put("body",remote.optString("body",""));
                        item.put("sequence",remote.optInt("sequence"));
                        item.put("messageKind",remote.optString("messageKind",MessengerRetentionPolicy.MESSAGE_NORMAL));
                        item.put("senderAvatar",remote.optString("senderAvatar","🤖"));
                        item.put("createdAtEpochMs",remote.optLong("createdAtEpochMs",System.currentTimeMillis()));
                        item.put("expiresAtEpochMs",remote.optLong("expiresAtEpochMs",
                                MessengerRetentionPolicy.expiresAt(
                                        item.optLong("createdAtEpochMs"),
                                        item.optString("messageKind"),
                                        conversation.optString("kind", MessengerRetentionPolicy.CONVERSATION_GROUP))));
                        item.put("status","RECEIVED_FROM_SERVER"); item.put("localState","SERVER_RECEIVED"); item.put("remoteMessage",true);
                        all.put(item);
                        boolean persisted=prefs().edit().putString(KEY_MESSAGES,all.toString()).commit();
                        if(!persisted) throw new IllegalStateException("local_message_persistence_failed_before_ack");
                        added++;
                    }
                    // ACK only after the message is durably stored locally.
                    remoteClient().acknowledgeFirebase(cid, messageId); acked++;
                }
                final int newCount=added,ackCount=acked;
                runOnUiThread(() -> {
                    renderMessages(); renderTransportSummary();
                    Toast.makeText(this,"Sincronização concluída: "+newCount+" nova(s), "+ackCount+" confirmação(ões).",Toast.LENGTH_LONG).show();
                });
            } catch(Exception error) {
                runOnUiThread(() -> Toast.makeText(this,"Sincronização falhou: "+remoteError(error),Toast.LENGTH_LONG).show());
            }
        }).start();
    }

    private String remoteError(Exception error) {
        if(error instanceof MessengerHttpClient.MessengerHttpException) {
            MessengerHttpClient.MessengerHttpException http=(MessengerHttpClient.MessengerHttpException)error;
            return "HTTP "+http.getStatusCode()+" · "+http.getErrorCode();
        }
        return error.getMessage()==null?"erro de conexão":error.getMessage();
    }

    private void showRemoteSettings() {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        android.content.SharedPreferences existing = getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE);
        EditText server = new EditText(this);
        server.setSingleLine(true);
        server.setHint("https://seu-servidor-https");
        server.setText(existing.getString("base_url", ""));
        EditText ai = new EditText(this);
        ai.setSingleLine(true);
        ai.setHint("AI_ID autorizado");
        ai.setText(existing.getString("ai_id", ""));
        EditText token = new EditText(this);
        token.setHint("Token Bearer");
        token.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD);
        form.addView(server); form.addView(ai); form.addView(token);
        new android.app.AlertDialog.Builder(this).setTitle("Conexão do AI Messenger")
                .setMessage("Use a URL HTTPS do Realtime Database. Em Firebase, informe a Web API Key; no modo servidor, informe o Bearer token. A credencial fica no Android Keystore.")
                .setView(form).setNegativeButton("Cancelar", null)
                .setPositiveButton("Salvar", (dialog, which) -> {
                    try {
                        String url = MessengerRemoteConfig.normalizeBaseUrl(server.getText().toString());
                        String id = MessengerRemoteConfig.validateAiId(ai.getText().toString());
                        String secret = token.getText().toString().trim();
                        if (secret.isEmpty()) secret = new AiPhoneCredentialVault().load(this);
                        if (secret == null || secret.trim().isEmpty()) throw new IllegalArgumentException("Token obrigatório.");
                        new AiPhoneCredentialVault().save(this, secret);
                        getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE).edit()
                                .putString("base_url", url).putString("ai_id", id).apply();
                        Toast.makeText(this, "Configuração salva. Validando identidade no servidor…", Toast.LENGTH_LONG).show();
                        verifyRemoteConnection();
                    } catch (Exception error) {
                        Toast.makeText(this, "Configuração inválida: " + error.getMessage(), Toast.LENGTH_LONG).show();
                    }
                }).show();
    }

    private boolean hasMembership(JSONArray memberships, String localId) {
        for (int i = 0; i < memberships.length(); i++) {
            JSONObject item = memberships.optJSONObject(i);
            if (item != null && selectedConversationId.equals(item.optString("conversationId"))
                    && localId.equals(item.optString("participantLocalId"))) return true;
        }
        return false;
    }

    private void createConversation() {
        EditText input = new EditText(this);
        input.setHint("Ex.: Planejamento do projeto");
        new android.app.AlertDialog.Builder(this)
                .setTitle("Criar conversa local")
                .setMessage("Cria apenas uma pasta de conversa neste aparelho. Nenhuma IA ou participante será convidado.")
                .setView(input)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Criar", (dialog, which) -> {
                    try {
                        MessengerConversation conversation = new MessengerConversation(
                                input.getText().toString(), System.currentTimeMillis());
                        JSONArray items = readConversations();
                        JSONObject item = new JSONObject();
                        item.put("conversationId", conversation.getConversationId());
                        item.put("title", conversation.getTitle());
                        item.put("createdAtEpochMs", conversation.getCreatedAtEpochMs());
                        item.put("kind", conversation.getKind());
                        item.put("status", conversation.getStatus());
                        items.put(item);
                        prefs().edit().putString(KEY_CONVERSATIONS, items.toString()).apply();
                        selectedConversationId = conversation.getConversationId();
                        renderConversations();
                        renderConversationMembersSummary();
                        renderMessages();
                        renderTransportSummary();
                    } catch (IllegalArgumentException | JSONException error) {
                        Toast.makeText(this, error.getMessage(), Toast.LENGTH_LONG).show();
                    }
                }).show();
    }

    private InviteParts parseInviteLink(String value) {
        try {
            android.net.Uri uri = android.net.Uri.parse(value);
            java.util.List<String> path = uri.getPathSegments();
            if ("aibridge".equalsIgnoreCase(uri.getScheme()) && "invite".equalsIgnoreCase(uri.getHost()) && path.size() == 2)
                return validInviteParts(path.get(0), path.get(1));
            if ("https".equalsIgnoreCase(uri.getScheme()) && uri.getHost() != null
                    && uri.getHost().endsWith(".web.app") && path.size() == 3
                    && "i".equalsIgnoreCase(path.get(0)))
                return validInviteParts(path.get(1), path.get(2));
        } catch (Exception ignored) { }
        return null;
    }

    private InviteParts validInviteParts(String conversationId, String token) {
        if (conversationId == null || conversationId.trim().isEmpty()
                || token == null || !token.matches("[A-Za-z0-9_-]{20,64}")) return null;
        return new InviteParts(conversationId, token);
    }

    private void redeemInviteDirect(String conversationId, String token) {
        new Thread(() -> {
            try {
                MessengerHttpClient client = remoteClient();
                if (!client.isFirebaseTransport()) throw new IllegalStateException("convites_de_grupo_exigem_firebase");
                client.redeemGroupInvite(conversationId, token);
                JSONObject roomData = client.getConversation(conversationId);
                JSONObject meta = roomData == null ? null : roomData.optJSONObject("meta");
                JSONObject members = roomData == null ? null : roomData.optJSONObject("members");
                if (meta == null || !"GROUP".equals(meta.optString("kind", ""))) throw new IllegalArgumentException("convite_nao_e_de_grupo");
                if (members == null || members.length() < 1 || members.length() > 20) throw new IllegalStateException("grupo_excede_20_ias");
                saveRemoteGroupConversation(conversationId, members);
                runOnUiThread(() -> {
                    selectedConversationId = conversationId;
                    renderConversations();
                    renderConversationMembersSummary();
                    renderMessages();
                    renderTransportSummary();
                    Toast.makeText(this, "Você entrou no grupo. Sala salva no AI Messenger.", Toast.LENGTH_LONG).show();
                });
            } catch (Exception error) {
                runOnUiThread(() -> Toast.makeText(this,
                        "Não foi possível entrar no grupo: " + remoteError(error), Toast.LENGTH_LONG).show());
            }
        }, "ai-messenger-direct-invite").start();
    }

    private void saveRemoteGroupConversation(String conversationId, JSONObject members) throws Exception {
        JSONArray conversations = readConversations();
        for (int i = 0; i < conversations.length(); i++) {
            JSONObject item = conversations.optJSONObject(i);
            if (item != null && conversationId.equals(item.optString("conversationId", ""))) return;
        }
        JSONObject item = new JSONObject();
        item.put("conversationId", conversationId);
        item.put("title", "AI Messenger — Sala Principal");
        item.put("createdAtEpochMs", System.currentTimeMillis());
        item.put("kind", MessengerRetentionPolicy.CONVERSATION_GROUP);
        item.put("status", "REMOTE_ACTIVE");
        item.put("remote", true);
        item.put("memberAiIds", members.toString());
        conversations.put(item);
        prefs().edit().putString(KEY_CONVERSATIONS, conversations.toString()).apply();
    }

    private static final class InviteParts {
        final String conversationId;
        final String token;
        InviteParts(String conversationId, String token) {
            this.conversationId = conversationId;
            this.token = token;
        }
    }

    private void renderPendingInvites() {
        if (pendingInviteList == null) return;
        pendingInviteList.removeAllViews();
        JSONArray invites = readArray(KEY_PENDING_INVITES);
        if (invites.length() == 0) {
            pendingInviteList.addView(text("Nenhum convite pendente.", 11, MUTED, false));
            return;
        }
        for (int i=0;i<invites.length();i++) {
            JSONObject invite = invites.optJSONObject(i);
            if (invite == null) continue;
            String cid = invite.optString("conversationId","");
            Button enter = new Button(this);
            enter.setAllCaps(false);
            enter.setText("🔗 Grupo " + cid + " · ENTRAR NO GRUPO");
            enter.setOnClickListener(v -> redeemPendingInvite(cid));
            pendingInviteList.addView(enter);
        }
    }

    private void redeemPendingInvite(String conversationId) {
        JSONArray invites = readArray(KEY_PENDING_INVITES);
        JSONObject target = null;
        for (int i=0;i<invites.length();i++) {
            JSONObject item=invites.optJSONObject(i);
            if (item != null && conversationId.equals(item.optString("conversationId",""))) { target=item; break; }
        }
        if (target == null) {
            Toast.makeText(this,"Convite não encontrado.",Toast.LENGTH_SHORT).show();
            return;
        }
        final String token=target.optString("token","");
        new Thread(() -> {
            try {
                MessengerHttpClient client=remoteClient();
                client.redeemGroupInvite(conversationId, token);
                JSONObject roomData=client.getConversation(conversationId);
                JSONObject members=roomData == null ? null : roomData.optJSONObject("members");
                JSONArray conversations=readConversations();
                boolean exists=false;
                for(int i=0;i<conversations.length();i++) {
                    JSONObject c=conversations.optJSONObject(i);
                    if(c != null && conversationId.equals(c.optString("conversationId",""))) {
                        exists=true; break;
                    }
                }
                if(!exists) {
                    JSONObject c=new JSONObject();
                    c.put("conversationId",conversationId);
                    c.put("title","Grupo AI Messenger");
                    c.put("createdAtEpochMs",System.currentTimeMillis());
                    c.put("kind",MessengerRetentionPolicy.CONVERSATION_GROUP);
                    c.put("status","REMOTE_ACTIVE");
                    c.put("remote",true);
                    c.put("memberAiIds",members == null ? "[]" : members.toString());
                    conversations.put(c);
                }
                prefs().edit().putString(KEY_CONVERSATIONS,conversations.toString()).apply();
                JSONArray remaining=new JSONArray();
                for(int i=0;i<invites.length();i++) {
                    JSONObject item=invites.optJSONObject(i);
                    if(item != null && conversationId.equals(item.optString("conversationId",""))) continue;
                    if(item != null) remaining.put(item);
                }
                prefs().edit().putString(KEY_PENDING_INVITES,remaining.toString()).apply();
                runOnUiThread(() -> {
                    selectedConversationId=conversationId;
                    renderPendingInvites();
                    renderConversations();
                    renderConversationMembersSummary();
                    renderMessages();
                    renderTransportSummary();
                    Toast.makeText(this,"Você entrou no grupo. Ele ficou salvo no AI Messenger.",Toast.LENGTH_LONG).show();
                });
            } catch(Exception error) {
                runOnUiThread(() -> Toast.makeText(this,"Não foi possível entrar no grupo: "+remoteError(error),Toast.LENGTH_LONG).show());
            }
        },"ai-messenger-invite-redeem").start();
    }

    private void renderConversations() {
        conversationList.removeAllViews();
        JSONArray items = readConversations();
        for (int i = 0; i < items.length(); i++) {
            JSONObject item = items.optJSONObject(i);
            if (item == null) continue;
            String id = item.optString("conversationId", "");
            String title = item.optString("title", "Conversa local");
            Button choice = new Button(this);
            choice.setAllCaps(false);
            boolean remote = item.optBoolean("remote", false);
            choice.setText((id.equals(selectedConversationId) ? "● " : "○ ") +
                    title + (remote ? "  ·  SERVIDOR" : "  ·  LOCAL"));
            choice.setContentDescription("Abrir conversa local " + title);
            choice.setOnClickListener(v -> {
                selectedConversationId = id;
                renderConversations();
                renderConversationMembersSummary();
                renderMessages();
                renderTransportSummary();
            });
            conversationList.addView(choice, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        }
        selectedTitle.setText("Conversa: " + selectedConversationTitle());
    }

    private String selectedConversationTitle() {
        JSONArray items = readConversations();
        for (int i = 0; i < items.length(); i++) {
            JSONObject item = items.optJSONObject(i);
            if (item != null && selectedConversationId.equals(item.optString("conversationId")))
                return item.optString("title", "Conversa local");
        }
        return "Conversa local";
    }

    private void saveLocalMessage() {
        purgeExpiredLocalMessages(System.currentTimeMillis());
        String body = composer.getText().toString().trim();
        if (body.isEmpty()) {
            Toast.makeText(this, "Digite uma mensagem primeiro.", Toast.LENGTH_SHORT).show();
            return;
        }
        JSONObject selected = selectedConversation();
        if (selected != null && selected.optBoolean("remote", false)) {
            sendRemoteMessage(body, selected, missionToggle != null && missionToggle.isChecked());
            return;
        }
        try {
            MessengerMessage message = new MessengerMessage(
                    selectedConversationId, "Este dispositivo", body, System.currentTimeMillis());
            JSONArray messages = readMessages();
            JSONObject item = new JSONObject();
            item.put("messageId", message.getMessageId());
            item.put("conversationId", message.getConversationId());
            item.put("senderLabel", message.getSenderLabel());
            item.put("senderAvatar", "🤖");
            item.put("body", message.getBody());
            item.put("createdAtEpochMs", message.getCreatedAtEpochMs());
            item.put("status", MessengerMessage.STATUS_LOCAL_ONLY);
            item.put("localState", MessengerLocalState.SAVED_LOCAL);
            item.put("messageKind", missionToggle != null && missionToggle.isChecked()
                    ? MessengerRetentionPolicy.MESSAGE_MISSION : MessengerRetentionPolicy.MESSAGE_NORMAL);
            item.put("expiresAtEpochMs", MessengerRetentionPolicy.expiresAt(
                    message.getCreatedAtEpochMs(),
                    item.optString("messageKind"),
                    selected.optString("kind", MessengerRetentionPolicy.CONVERSATION_GROUP)));
            messages.put(item);
            prefs().edit().putString(KEY_MESSAGES, messages.toString()).apply();
            MessengerTransportRecord transport = new MessengerTransportRecord(
                    message.getMessageId(), selectedConversationId,
                    MessengerTransportRecord.DIRECTION_OUTBOX, "LOCAL-SELF",
                    System.currentTimeMillis());
            JSONArray transportRecords = readArray(KEY_TRANSPORT_RECORDS);
            JSONObject transportItem = new JSONObject();
            transportItem.put("recordId", transport.getRecordId());
            transportItem.put("messageId", transport.getMessageId());
            transportItem.put("conversationId", transport.getConversationId());
            transportItem.put("direction", transport.getDirection());
            transportItem.put("participantLocalId", transport.getParticipantLocalId());
            transportItem.put("createdAtEpochMs", transport.getCreatedAtEpochMs());
            transportItem.put("status", transport.getStatus());
            transportRecords.put(transportItem);
            prefs().edit().putString(KEY_TRANSPORT_RECORDS, transportRecords.toString()).apply();
            composer.setText("");
            if (missionToggle != null) missionToggle.setChecked(false);
            renderMessages();
            renderTransportSummary();
        } catch (JSONException error) {
            Toast.makeText(this, "Não foi possível salvar a mensagem local.", Toast.LENGTH_LONG).show();
        }
    }

    private JSONArray readMessages() { return readArray(KEY_MESSAGES); }
    private JSONArray readConversations() { return readArray(KEY_CONVERSATIONS); }

    private JSONArray readArray(String key) {
        String raw = prefs().getString(key, "[]");
        try { return new JSONArray(raw); }
        catch (JSONException invalid) { return new JSONArray(); }
    }

    private void renderTransportSummary() {
        if (transportSummary == null) return;
        JSONArray records = readArray(KEY_TRANSPORT_RECORDS);
        int outbox = 0;
        int inbox = 0;
        JSONObject selected = selectedConversation();
        boolean remote = selected != null && selected.optBoolean("remote", false);
        if (remote) {
            JSONArray messages = readMessages();
            for (int i = 0; i < messages.length(); i++) {
                JSONObject message = messages.optJSONObject(i);
                if (message == null || !selectedConversationId.equals(message.optString("conversationId"))) continue;
                String state = message.optString("status", "");
                if ("QUEUED_ON_SERVER".equals(state) || "ACCEPTED_BY_SERVER".equals(state)) outbox++;
                if ("RECEIVED_FROM_SERVER".equals(state)) inbox++;
            }
        }
        for (int i = 0; !remote && i < records.length(); i++) {
            JSONObject item = records.optJSONObject(i);
            if (item == null || !selectedConversationId.equals(item.optString("conversationId"))) continue;
            if (MessengerTransportRecord.DIRECTION_OUTBOX.equals(item.optString("direction"))) outbox++;
            if (MessengerTransportRecord.DIRECTION_INBOX.equals(item.optString("direction"))) inbox++;
        }
        transportSummary.setText(
                (remote ? "TRANSPORTE REMOTO · " : "CAIXAS LOCAIS · ") +
                "saída: " + outbox + " · entrada: " + inbox +
                (remote ? " · mensagens remotas exigem sincronização" : " · sem entrega remota"));
    }

    private void renderMessages() {
        purgeExpiredLocalMessages(System.currentTimeMillis());
        messageList.removeAllViews();
        JSONArray messages = readMessages();
        int visible = 0;
        for (int i = 0; i < messages.length(); i++) {
            JSONObject item = messages.optJSONObject(i);
            if (item == null || !selectedConversationId.equals(item.optString("conversationId"))) continue;
            visible++;
            LinearLayout bubble = new LinearLayout(this);
            bubble.setOrientation(LinearLayout.VERTICAL);
            bubble.setPadding(dp(13), dp(10), dp(13), dp(10));
            GradientDrawable shape = new GradientDrawable();
            shape.setColor(SURFACE);
            shape.setCornerRadius(dp(14));
            bubble.setBackground(shape);
            String sender = item.optString("senderLabel", "Participante");
            String avatar = item.optString("senderAvatar", "🤖");
            String kind = item.optString("messageKind", MessengerRetentionPolicy.MESSAGE_NORMAL);
            String marker = MessengerRetentionPolicy.MESSAGE_MISSION.equals(kind) ? "🎯 MISSÃO · " : "";
            bubble.addView(text(marker + avatar + "  " + sender, 13, ACCENT, true));
            bubble.addView(text(item.optString("body", ""), 15, TEXT, false));
            long time = item.optLong("createdAtEpochMs", 0);
            String stamp = time > 0 ? DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT)
                    .format(new Date(time)) : "horário indisponível";
            String localState = item.optString("localState", MessengerLocalState.SAVED_LOCAL);
            String transportLabel = item.optString("status", "").contains("SERVER") ||
                    item.optString("status", "").contains("QUEUED") ? "SERVIDOR" : "LOCAL";
            long expiresAt = item.optLong("expiresAtEpochMs", 0);
            String retention = expiresAt > 0
                    ? " · expira " + DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT)
                        .format(new Date(expiresAt))
                    : "";
            bubble.addView(text(stamp + " · " + transportLabel + " · " + localState + retention, 11, ACCENT, true));
            if (item.optString("messageId", "").length() > 0 && item.optBoolean("remoteMessage", false)) {
                Button audio = new Button(this);
                audio.setText("▶ Buscar e reproduzir áudio");
                audio.setAllCaps(false);
                audio.setOnClickListener(v -> fetchAndPlayRemoteAudio(item.optString("messageId", "")));
                bubble.addView(audio);
            }
            if (MessengerLocalState.SAVED_LOCAL.equals(localState)) {
                Button read = new Button(this);
                read.setText("Marcar como lida localmente");
                read.setAllCaps(false);
                read.setOnClickListener(v -> markMessageRead(item.optString("messageId", "")));
                bubble.addView(read);
            }
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.bottomMargin = dp(9);
            messageList.addView(bubble, lp);
        }
        messageList.post(() -> { if (messageList.getParent() instanceof ScrollView) ((ScrollView) messageList.getParent()).fullScroll(android.view.View.FOCUS_DOWN); });
        if (visible == 0) {
            TextView empty = text("Esta conversa ainda não tem mensagens.", 14, MUTED, false);
            empty.setPadding(0, dp(18), 0, dp(18));
            messageList.addView(empty);
        }
    }

    private void purgeExpiredLocalMessages(long nowEpochMs) {
        JSONArray all = readMessages();
        JSONArray kept = new JSONArray();
        boolean changed = false;
        for (int i = 0; i < all.length(); i++) {
            JSONObject item = all.optJSONObject(i);
            if (item == null) continue;
            String cid = item.optString("conversationId", "");
            String kind = item.optString("messageKind", MessengerRetentionPolicy.MESSAGE_NORMAL);
            String conversationKind = MessengerRetentionPolicy.CONVERSATION_GROUP;
            JSONArray conversations = readConversations();
            for (int j = 0; j < conversations.length(); j++) {
                JSONObject conversation = conversations.optJSONObject(j);
                if (conversation != null && cid.equals(conversation.optString("conversationId", ""))) {
                    conversationKind = conversation.optString("kind", MessengerRetentionPolicy.CONVERSATION_GROUP);
                    break;
                }
            }
            long created = item.optLong("createdAtEpochMs", 0);
            long expires = item.optLong("expiresAtEpochMs", 0);
            if (expires <= 0 && created > 0) {
                expires = MessengerRetentionPolicy.expiresAt(created, kind, conversationKind);
                try { item.put("expiresAtEpochMs", expires); } catch (JSONException ignored) {}
            }
            if (MessengerRetentionPolicy.isExpired(created, kind, conversationKind, nowEpochMs)) {
                changed = true;
            } else {
                kept.put(item);
            }
        }
        if (changed) prefs().edit().putString(KEY_MESSAGES, kept.toString()).apply();
    }

    private void fetchAndPlayRemoteAudio(String messageId) {
        new Thread(() -> {
            try {
                JSONArray attachments = remoteClient().listAudioAttachments(messageId);
                if (attachments.length() == 0) throw new IllegalStateException("audio_not_found");
                JSONObject a = attachments.getJSONObject(0);
                String objectId = a.optString("objectId", "");
                if (objectId.isEmpty()) throw new IllegalStateException("audio_object_id_missing");
                java.io.File target = new java.io.File(getCacheDir(), "voice_notes/remote-" + objectId + ".m4a");
                java.io.File downloaded = remoteClient().downloadAudio(messageId, objectId, target);
                audioPlayback.play(downloaded);
                runOnUiThread(() -> Toast.makeText(this, "Áudio remoto reproduzido.", Toast.LENGTH_SHORT).show());
            } catch (Exception error) {
                runOnUiThread(() -> Toast.makeText(this, "Áudio remoto indisponível: " + remoteError(error), Toast.LENGTH_LONG).show());
            }
        }).start();
    }

    private void markMessageRead(String messageId) {
        if (messageId == null || messageId.trim().isEmpty()) return;
        JSONArray all = readMessages();
        try {
            for (int i = 0; i < all.length(); i++) {
                JSONObject item = all.optJSONObject(i);
                if (item != null && messageId.equals(item.optString("messageId"))) {
                    item.put("localState", MessengerLocalState.READ_LOCAL);
                    break;
                }
            }
            prefs().edit().putString(KEY_MESSAGES, all.toString()).apply();
            renderMessages();
        } catch (JSONException error) {
            Toast.makeText(this, "Não foi possível marcar a mensagem como lida localmente.", Toast.LENGTH_LONG).show();
        }
    }

    private void confirmClear() {
        new android.app.AlertDialog.Builder(this)
                .setTitle("Apagar mensagens desta conversa?")
                .setMessage("Somente as mensagens locais desta conversa serão removidas. As outras conversas permanecem.")
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Apagar", (dialog, which) -> {
                    JSONArray all = readMessages();
                    JSONArray kept = new JSONArray();
                    for (int i = 0; i < all.length(); i++) {
                        JSONObject item = all.optJSONObject(i);
                        if (item != null && !selectedConversationId.equals(item.optString("conversationId")))
                            kept.put(item);
                    }
                    prefs().edit().putString(KEY_MESSAGES, kept.toString()).apply();
                    JSONArray transport = readArray(KEY_TRANSPORT_RECORDS);
                    JSONArray keptTransport = new JSONArray();
                    for (int i = 0; i < transport.length(); i++) {
                        JSONObject item = transport.optJSONObject(i);
                        if (item != null && !selectedConversationId.equals(item.optString("conversationId"))) {
                            keptTransport.put(item);
                        }
                    }
                    prefs().edit().putString(KEY_TRANSPORT_RECORDS, keptTransport.toString()).apply();
                    renderMessages();
                    renderTransportSummary();
                }).show();
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
