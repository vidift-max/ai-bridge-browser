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

public final class MessengerActivity extends Activity {
    private static final String PREFS = "ai_messenger_local_v1";
    private static final String KEY_MESSAGES = "local_messages";
    private static final String KEY_CONVERSATIONS = "local_conversations";
    private static final String KEY_PARTICIPANTS = "local_participants";
    private static final String KEY_MEMBERSHIPS = "local_memberships";
    private static final String KEY_INVITATIONS = "local_invitation_drafts";
    private static final String KEY_TRANSPORT_RECORDS = "local_transport_records";
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
    private TextView selectedTitle;
    private TextView memberSummary;
    private TextView transportSummary;
    private String selectedConversationId = DEFAULT_ID;

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
        page.addView(text("Conversas locais · sem participantes remotos conectados", 13, MUTED, false));
        page.addView(text("LOCAL ONLY — nada é enviado pela internet.", 12, ACCENT, true));

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
        page.addView(text("HISTÓRICO · LOCAL ONLY", 11, ACCENT, true));

        ScrollView scroll = new ScrollView(this);
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
        Button save = new Button(this);
        save.setText("Salvar");
        save.setAllCaps(false);
        save.setOnClickListener(v -> saveLocalMessage());
        entry.addView(save);
        page.addView(entry);
        Button clear = new Button(this);
        clear.setText("Apagar mensagens desta conversa");
        clear.setAllCaps(false);
        clear.setOnClickListener(v -> confirmClear());
        page.addView(clear);
        setContentView(page);
        renderConversations();
        renderParticipants();
        renderMessages();
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
            choice.setText((id.equals(selectedConversationId) ? "● " : "○ ") +
                    title + "  ·  LOCAL ONLY");
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
        String body = composer.getText().toString().trim();
        if (body.isEmpty()) {
            Toast.makeText(this, "Digite uma mensagem primeiro.", Toast.LENGTH_SHORT).show();
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
            item.put("body", message.getBody());
            item.put("createdAtEpochMs", message.getCreatedAtEpochMs());
            item.put("status", MessengerMessage.STATUS_LOCAL_ONLY);
            item.put("localState", MessengerLocalState.SAVED_LOCAL);
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
        for (int i = 0; i < records.length(); i++) {
            JSONObject item = records.optJSONObject(i);
            if (item == null || !selectedConversationId.equals(item.optString("conversationId"))) continue;
            if (MessengerTransportRecord.DIRECTION_OUTBOX.equals(item.optString("direction"))) outbox++;
            if (MessengerTransportRecord.DIRECTION_INBOX.equals(item.optString("direction"))) inbox++;
        }
        transportSummary.setText(
                "CAIXAS LOCAIS · saída: " + outbox + " · entrada: " + inbox +
                " · LOCAL ONLY · nenhum registro comprova entrega remota");
    }

    private void renderMessages() {
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
            bubble.addView(text(item.optString("body", ""), 15, TEXT, false));
            long time = item.optLong("createdAtEpochMs", 0);
            String stamp = time > 0 ? DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT)
                    .format(new Date(time)) : "horário indisponível";
            String localState = item.optString("localState", MessengerLocalState.SAVED_LOCAL);
            bubble.addView(text(stamp + " · LOCAL ONLY · " + localState, 11, ACCENT, true));
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
        if (visible == 0) {
            TextView empty = text("Esta conversa ainda não tem mensagens locais.", 14, MUTED, false);
            empty.setPadding(0, dp(18), 0, dp(18));
            messageList.addView(empty);
        }
    }

    private void markMessageRead(String messageId) {
        if (messageId == null || messageId.trim().isEmpty()) return;
        JSONArray all = readMessages();
        for (int i = 0; i < all.length(); i++) {
            JSONObject item = all.optJSONObject(i);
            if (item != null && messageId.equals(item.optString("messageId"))) {
                item.put("localState", MessengerLocalState.READ_LOCAL);
                break;
            }
        }
        prefs().edit().putString(KEY_MESSAGES, all.toString()).apply();
        renderMessages();
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
