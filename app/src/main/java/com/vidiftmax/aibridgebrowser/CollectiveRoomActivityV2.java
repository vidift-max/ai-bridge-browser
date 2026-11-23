package com.vidiftmax.aibridgebrowser;

import android.app.Activity;
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
import android.widget.Toast;
import android.graphics.drawable.GradientDrawable;
import java.io.File;
import java.io.FileOutputStream;
import java.text.DateFormat;
import java.util.Date;
import java.util.HashSet;
import java.util.Set;
import org.json.JSONArray;
import org.json.JSONObject;

public final class CollectiveRoomActivityV2 extends Activity {
    private static final String PREFS="ai_collective_room_v2";
    private static final String MESSENGER_PREFS="ai_messenger_local_v1";
    private static final String REMOTE_PREFS="ai_phone_registry_config_v1";
    private static final String REMOTE_IDS="remote_message_ids";
    private String remoteConversationId="";
    private JSONArray remoteMemberAiIds=new JSONArray();
    private TextView remoteStatus;
    private TextView callStatus;
    private volatile String activeVoiceCallId = "";
    private volatile WebRtcVoiceEngine webRtcVoiceEngine;
    private volatile boolean voiceSignalPolling;
    private volatile boolean voiceOfferCreated;
    private volatile boolean remoteSdpReady;
    private volatile boolean voiceCallConnected;
    private volatile long lastVoiceSignalId;
    private final VoiceIceCandidateBuffer pendingRemoteIce = new VoiceIceCandidateBuffer();
    private String pendingVoicePermissionAction = "";
    private int previousAudioMode = -1;
    private volatile boolean remoteOperationRunning;
    private static final int BG=0xFF101827,SURFACE=0xFF1B293B,TEXT=0xFFF4F7FB,MUTED=0xFFB5C2D1,ACCENT=0xFF55D6BE;
    private LinearLayout presenceList,messageList;
    private EditText composer;
    private String myName,myAvatar;
    private android.widget.CheckBox missionToggle;
    private Button audioButton, microphoneButton, voiceMuteButton;
    private volatile boolean voiceCallMuted;
    private boolean audioOpen, microphoneOpen;
    private AudioMonitor audioMonitor;
    private final AudioRecorder voiceNoteRecorder=new AudioRecorder();
    private final AudioPlayback voiceNotePlayback=new AudioPlayback();
    private File lastRemoteVoiceNote;

    @Override protected void onCreate(Bundle state){
        super.onCreate(state);
        myName=prefs().getString("profile_name","Minha IA");
        myAvatar=prefs().getString("profile_avatar","🤖");
        audioOpen=prefs().getBoolean("audio_room_open",false);
        microphoneOpen=false;
        prefs().edit().putBoolean("microphone_open",false).apply();
        audioMonitor=new AudioMonitor();
        audioMonitor.setPlaybackEnabled(audioOpen);

        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.HORIZONTAL);
        root.setPadding(dp(10),dp(10),dp(10),dp(10));
        root.setBackgroundColor(BG);

        LinearLayout chatColumn=new LinearLayout(this);
        chatColumn.setOrientation(LinearLayout.VERTICAL);
        chatColumn.setPadding(dp(4),dp(2),dp(8),dp(2));

        LinearLayout header=new LinearLayout(this);
        header.setOrientation(LinearLayout.VERTICAL);
        header.addView(text("SALA COLETIVA · AI MESSENGER",21,TEXT,true));
        header.addView(text("Conversa principal · participantes aparecem no painel à direita.",12,MUTED,false));
        header.addView(button("✎ Meu perfil · "+myAvatar+" "+myName,v->editProfile()));
        header.addView(button("＋ Entrar na sala coletiva",v->enterRoom()));
        header.addView(button("🔐 Configurar AI Messenger remoto",v->startActivity(new Intent(this,MessengerActivity.class))));
        header.addView(button("🔗 Vincular conversa remota",v->chooseRemoteConversation()));
        header.addView(button("🔢 Vincular por ID e AI_IDs",v->linkRemoteConversationById()));
        header.addView(button("🔗 Criar link de convite do grupo",v->createGroupInviteLink()));
        header.addView(button("↻ Sincronizar mensagens",v->syncRemoteRoom()));
        remoteStatus=text("Sala em modo local · nenhuma conversa remota vinculada.",11,MUTED,false);
        remoteStatus.setTextIsSelectable(true);
        header.addView(remoteStatus);
        LinearLayout callRow = new LinearLayout(this);
        callRow.setOrientation(LinearLayout.HORIZONTAL);
        callRow.addView(button("📞 Ligar",v->startVoiceCall()),new LinearLayout.LayoutParams(0,-2,1));
        callRow.addView(button("📲 Atender",v->answerVoiceCall()),new LinearLayout.LayoutParams(0,-2,1));
        callRow.addView(button("Recusar",v->rejectVoiceCall()),new LinearLayout.LayoutParams(0,-2,1));
        callRow.addView(button("Desligar",v->endVoiceCall()),new LinearLayout.LayoutParams(0,-2,1));
        callRow.addView(button("↻ Chamada",v->refreshVoiceCall()),new LinearLayout.LayoutParams(0,-2,1));
        callRow.addView(button("⚙ ICE",v->configureVoiceIceServers()),new LinearLayout.LayoutParams(0,-2,1));
        header.addView(callRow);
        voiceMuteButton = button("🎙️ Silenciar na chamada",v->toggleVoiceCallMute());
        header.addView(voiceMuteButton);
        updateVoiceCallMuteButton();
        callStatus = text("Chamadas WebRTC de áudio · requer microfone autorizado e conectividade ICE.",10,MUTED,false);
        header.addView(callStatus);

        LinearLayout quickActions=new LinearLayout(this);
        quickActions.setOrientation(LinearLayout.HORIZONTAL);
        quickActions.addView(button("📄 Compromisso",v->openPdf(true)),
                new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1));
        quickActions.addView(button("📄 Contrato",v->openPdf(false)),
                new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1));
        header.addView(quickActions);
        chatColumn.addView(header);

        chatColumn.addView(text("MENSAGENS DA SALA",11,ACCENT,true));
        ScrollView ms=new ScrollView(this);
        messageList=new LinearLayout(this);
        messageList.setOrientation(LinearLayout.VERTICAL);
        ms.setFillViewport(true);
        ms.setVerticalScrollBarEnabled(true);
        ms.addView(messageList,new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));
        chatColumn.addView(ms,new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,0,1));

        LinearLayout composerArea=new LinearLayout(this);
        composerArea.setOrientation(LinearLayout.VERTICAL);
        composer=new EditText(this);
        composer.setHint("Falando com todos...");
        composer.setTextColor(TEXT);
        composer.setHintTextColor(MUTED);
        composer.setMinLines(2);
        composer.setGravity(android.view.Gravity.TOP);
        composerArea.addView(composer,new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,dp(70)));
        LinearLayout sendRow=new LinearLayout(this);
        sendRow.setOrientation(LinearLayout.HORIZONTAL);
        missionToggle = new android.widget.CheckBox(this);
        missionToggle.setText("🎯 MISSÃO · 24h");
        missionToggle.setTextColor(ACCENT);
        missionToggle.setAllCaps(false);
        sendRow.addView(missionToggle,new LinearLayout.LayoutParams(0,-2,1));
        sendRow.addView(button("Enviar",v->sendMessage()),
                new LinearLayout.LayoutParams(dp(105),ViewGroup.LayoutParams.WRAP_CONTENT));
        composerArea.addView(sendRow);
        LinearLayout voiceNotes=new LinearLayout(this);
        voiceNotes.setOrientation(LinearLayout.HORIZONTAL);
        voiceNotes.addView(button("🎙 Gravar nota",v->startVoiceNote()),new LinearLayout.LayoutParams(0,-2,1));
        voiceNotes.addView(button("Parar",v->stopVoiceNote()),new LinearLayout.LayoutParams(0,-2,1));
        voiceNotes.addView(button("Enviar áudio",v->sendVoiceNote()),new LinearLayout.LayoutParams(0,-2,1));
        voiceNotes.addView(button("▶ Ouvir recebida",v->playRemoteVoiceNote()),new LinearLayout.LayoutParams(0,-2,1));
        composerArea.addView(voiceNotes);
        composerArea.addView(text("Notas de voz remotas usam o servidor autenticado. O microfone de retorno local não é uma chamada ao vivo.",10,MUTED,false));
        chatColumn.addView(composerArea);

        root.addView(chatColumn,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.MATCH_PARENT,1));

        LinearLayout participantColumn=new LinearLayout(this);
        participantColumn.setOrientation(LinearLayout.VERTICAL);
        participantColumn.setPadding(dp(8),dp(2),dp(2),dp(2));
        GradientDrawable panelBg=new GradientDrawable();
        panelBg.setColor(SURFACE);
        panelBg.setCornerRadius(dp(16));
        participantColumn.setBackground(panelBg);
        participantColumn.addView(text("PARTICIPANTES",15,TEXT,true));
        participantColumn.addView(text("Todos nesta sala",10,MUTED,false));
        ScrollView ps=new ScrollView(this);
        presenceList=new LinearLayout(this);
        presenceList.setOrientation(LinearLayout.VERTICAL);
        ps.addView(presenceList);
        participantColumn.addView(ps,new LinearLayout.LayoutParams(0,0,1));
        participantColumn.addView(button("＋ Adicionar",v->addParticipant()));
        LinearLayout voiceRow=new LinearLayout(this);
        voiceRow.setOrientation(LinearLayout.HORIZONTAL);
        audioButton=button("🔊 Ouvir voz",v->toggleAudioRoom());
        microphoneButton=button("🎙️",v->toggleMicrophone());
        voiceRow.addView(audioButton,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1));
        voiceRow.addView(microphoneButton,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1));
        participantColumn.addView(voiceRow);
        updateAudioButton();
        updateMicrophoneButton();
        participantColumn.addView(text("🔊 Ouvir voz: ativa/desativa o retorno local. 🎙️ Microfone: captura sua voz. Para ouvir sua própria voz, ative os dois controles e use fones. Isso não transmite voz às outras IAs.",10,MUTED,false));

        int widthDp=getResources().getConfiguration().screenWidthDp;
        int panelWidth=widthDp>=700?dp(235):dp(155);
        root.addView(participantColumn,new LinearLayout.LayoutParams(panelWidth,ViewGroup.LayoutParams.MATCH_PARENT));

        setContentView(root);
        renderPresence();
        renderMessages();
        handleInviteIntent(getIntent());
    }

    private Button button(String s,android.view.View.OnClickListener l){ Button b=new Button(this); b.setText(s); b.setAllCaps(false); b.setOnClickListener(l); return b; }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleInviteIntent(intent);
    }

    private void handleInviteIntent(Intent intent) {
        if (intent == null) return;
        String cid = intent.getStringExtra("invite_conversation_id");
        if (cid == null || cid.trim().isEmpty()) return;
        remoteConversationId = cid.trim();
        try {
            JSONObject members = new JSONObject(intent.getStringExtra("invite_members", "{}"));
            JSONArray ids = new JSONArray();
            java.util.Iterator<String> keys = members.keys();
            while (keys.hasNext()) ids.put(keys.next());
            remoteMemberAiIds = ids;
            prefs().edit().putString("remote_conversation_id", remoteConversationId)
                    .putString("remote_member_ai_ids", ids.toString()).apply();
        } catch (Exception ignored) { }
        remoteStatus.setText("Sala remota vinculada pelo convite · " + remoteConversationId);
        syncRemoteRoom();
    }

    private void createGroupInviteLink() {
        if (remoteConversationId == null || remoteConversationId.trim().isEmpty()) {
            Toast.makeText(this, "Primeiro vincule uma conversa remota de grupo.", Toast.LENGTH_LONG).show();
            return;
        }
        new Thread(() -> {
            try {
                long expires = System.currentTimeMillis() + 7L * 24L * 60L * 60L * 1000L;
                JSONObject result = remoteClient().createGroupInvite(remoteConversationId, expires);
                String link = result.optString("link", "");
                runOnUiThread(() -> {
                    android.content.ClipboardManager cb = (android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
                    cb.setPrimaryClip(android.content.ClipData.newPlainText("Convite AI Messenger", link));
                    Intent share = new Intent(Intent.ACTION_SEND);
                    share.setType("text/plain");
                    share.putExtra(Intent.EXTRA_TEXT, "Entre na sala do AI Messenger por este link:\n" + link);
                    Toast.makeText(this, "Link criado e copiado. Expira em 7 dias.", Toast.LENGTH_LONG).show();
                    startActivity(Intent.createChooser(share, "Compartilhar convite"));
                });
            } catch (Exception error) {
                runOnUiThread(() -> Toast.makeText(this, "Não foi possível criar o convite: " + error.getMessage(), Toast.LENGTH_LONG).show());
            }
        }, "ai-messenger-invite-create").start();
    }

    private void toggleAudioRoom(){
        audioOpen=!audioOpen;
        audioMonitor.setPlaybackEnabled(audioOpen);
        prefs().edit().putBoolean("audio_room_open",audioOpen).apply();
        updateAudioButton();
        android.widget.Toast.makeText(this,
                audioOpen ? "Retorno de áudio local ativado. Ligue o microfone para ouvir sua voz." : "Retorno de áudio local desativado.",
                android.widget.Toast.LENGTH_SHORT).show();
    }

    private void toggleMicrophone(){
        if (microphoneOpen) {
            microphoneOpen=false;
            audioMonitor.stop();
            prefs().edit().putBoolean("microphone_open",false).apply();
            updateMicrophoneButton();
            android.widget.Toast.makeText(this,"Microfone desativado.",android.widget.Toast.LENGTH_SHORT).show();
            return;
        }
        if (android.os.Build.VERSION.SDK_INT >= 23 && checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{android.Manifest.permission.RECORD_AUDIO}, 7001);
            return;
        }
        try {
            audioMonitor.start();
            microphoneOpen=true;
            prefs().edit().putBoolean("microphone_open",true).apply();
            updateMicrophoneButton();
            android.widget.Toast.makeText(this,"Microfone ativado. Use fones para evitar microfonia.",android.widget.Toast.LENGTH_LONG).show();
        } catch (Exception error) {
            microphoneOpen=false;
            android.widget.Toast.makeText(this,"Microfone indisponível: "+error.getMessage(),android.widget.Toast.LENGTH_LONG).show();
        }
    }

    private void updateMicrophoneButton(){
        if(microphoneButton==null)return;
        microphoneButton.setText(microphoneOpen ? "🎙️ ON" : "🎙️ OFF");
        microphoneButton.setContentDescription(microphoneOpen ? "Desativar microfone" : "Ativar microfone e ouvir sua voz");
    }

    @Override public void onRequestPermissionsResult(int requestCode,String[] permissions,int[] grantResults){
        super.onRequestPermissionsResult(requestCode,permissions,grantResults);
        if (requestCode == 7201) {
            String action = pendingVoicePermissionAction;
            pendingVoicePermissionAction = "";
            if (grantResults.length > 0
                    && grantResults[0] == android.content.pm.PackageManager.PERMISSION_GRANTED) {
                if ("start".equals(action)) startVoiceCall();
                else if ("accept".equals(action)) answerVoiceCall();
            } else {
                Toast.makeText(this, "Permissão do microfone negada. A chamada não foi iniciada.",
                        Toast.LENGTH_LONG).show();
            }
            return;
        }
        if(grantResults.length>0 && grantResults[0]==android.content.pm.PackageManager.PERMISSION_GRANTED){
            if(requestCode==7001) toggleMicrophone();
            else if(requestCode==7101) startVoiceNote();
        }
    }

    @Override protected void onPause(){
        super.onPause();
        if(microphoneOpen){ microphoneOpen=false; audioMonitor.stop(); prefs().edit().putBoolean("microphone_open",false).apply(); updateMicrophoneButton(); }
        voiceNoteRecorder.cancel();
        if (webRtcVoiceEngine != null) {
            final String callId = activeVoiceCallId;
            stopVoiceMedia(); // Always stop local capture immediately when leaving the call screen.
            if (callId != null && !callId.isEmpty()) {
                new Thread(() -> {
                    try {
                        MessengerHttpClient client = remoteClient();
                        JSONObject call = client.getVoiceCall(callId);
                        String state = call.optString("state", "UNKNOWN");
                        String own = getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE).getString("ai_id", "");
                        String caller = call.optString("caller_ai_id", "");
                        String action = "RINGING".equals(state)
                                ? (own.equals(caller) ? "cancel" : "reject") : "end";
                        client.voiceCallAction(callId, action);
                    } catch (Exception ignored) { /* Local microphone is already closed. */ }
                }, "ai-voice-call-background-stop").start();
            }
        }
    }

    @Override protected void onDestroy(){
        if(audioMonitor!=null) audioMonitor.stop();
        microphoneOpen=false;
        stopVoiceMedia();
        super.onDestroy();
    }

    private void updateAudioButton(){
        if(audioButton==null)return;
        audioButton.setText(audioOpen ? "🔊 Ouvir voz · ON" : "🔊 Ouvir voz · OFF");
        audioButton.setContentDescription(audioOpen
                ? "Desativar retorno de áudio local"
                : "Ativar retorno de áudio local");
    }

    private void editProfile(){
        LinearLayout form=new LinearLayout(this); form.setOrientation(LinearLayout.VERTICAL);
        EditText name=new EditText(this); name.setHint("Nome da IA"); name.setText(myName); form.addView(name);
        String[] icons={"🤖","🧠","💡","🔬","🛠️","🚀","📚","🌐","⭐","🦾"};
        LinearLayout row=new LinearLayout(this); row.setOrientation(LinearLayout.HORIZONTAL);
        for(String icon:icons){ Button b=button(icon,v->myAvatar=((Button)v).getText().toString()); row.addView(b,new LinearLayout.LayoutParams(0,dp(52),1)); }
        form.addView(row);
        new android.app.AlertDialog.Builder(this).setTitle("Meu perfil")
            .setMessage("Escolha o ícone que será mostrado na sala. A identidade AI_ID permanece separada.")
            .setView(form).setNegativeButton("Cancelar",null)
            .setPositiveButton("Salvar",(d,w)->{ myName=name.getText().toString().trim(); if(myName.isEmpty())myName="Minha IA";
                prefs().edit().putString("profile_name",myName).putString("profile_avatar",myAvatar).apply(); renderPresence(); }).show();
    }

    private MessengerHttpClient remoteClient() throws Exception {
        android.content.SharedPreferences config=getSharedPreferences(REMOTE_PREFS,MODE_PRIVATE);
        return new MessengerHttpClient(this, config.getString("base_url",null),config.getString("ai_id",null),
                new AiPhoneCredentialVault().load(this));
    }

    private void chooseRemoteConversation(){
        JSONArray conversations;
        try { conversations=new JSONArray(getSharedPreferences(MESSENGER_PREFS,MODE_PRIVATE).getString("local_conversations","[]")); }
        catch(Exception invalid){ Toast.makeText(this,"Lista de conversas remotas inválida.",Toast.LENGTH_LONG).show(); return; }
        java.util.ArrayList<JSONObject> choices=new java.util.ArrayList<>();
        java.util.ArrayList<String> labels=new java.util.ArrayList<>();
        for(int i=0;i<conversations.length();i++){
            JSONObject item=conversations.optJSONObject(i);
            if(item!=null && item.optBoolean("remote",false)){
                JSONArray members=item.optJSONArray("remoteMemberAiIds");
                if(members!=null && members.length()>=2){
                    choices.add(item);
                    labels.add(item.optString("title","Conversa remota")+" · "+item.optString("kind","GROUP")+" · "+members.length()+" membros");
                }
            }
        }
        if(choices.isEmpty()){
            new android.app.AlertDialog.Builder(this).setTitle("Nenhuma conversa remota")
                    .setMessage("Configure o servidor e crie uma conversa remota no AI Messenger. Depois volte aqui para vinculá-la à Sala Coletiva.")
                    .setPositiveButton("Abrir configuração",(d,w)->startActivity(new Intent(this,MessengerActivity.class)))
                    .setNegativeButton("Fechar",null).show();
            return;
        }
        new android.app.AlertDialog.Builder(this).setTitle("Vincular Sala Coletiva a uma conversa remota")
                .setItems(labels.toArray(new String[0]),(d,which)->{
                    JSONObject selected=choices.get(which);
                    remoteConversationId=selected.optString("conversationId","");
                    remoteMemberAiIds=selected.optJSONArray("remoteMemberAiIds");
                    if(remoteMemberAiIds==null)remoteMemberAiIds=new JSONArray();
                    prefs().edit().putString("remote_conversation_id",remoteConversationId)
                            .putString("remote_member_ai_ids",remoteMemberAiIds.toString()).apply();
                    updateRemoteStatus();
                    Toast.makeText(this,"Conversa remota vinculada. Sincronize para buscar mensagens.",Toast.LENGTH_LONG).show();
                }).setNegativeButton("Cancelar",null).show();
    }

    private void linkRemoteConversationById() {
        android.content.SharedPreferences config = getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE);
        String own = config.getString("ai_id", "");
        if (own.trim().isEmpty()) {
            Toast.makeText(this, "Configure e valide seu AI_ID no AI Messenger primeiro.", Toast.LENGTH_LONG).show();
            return;
        }
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        EditText conversation = new EditText(this);
        conversation.setSingleLine(true);
        conversation.setHint("ID exato da conversa remota");
        EditText members = new EditText(this);
        members.setHint("Outros AI_IDs, separados por vírgula");
        form.addView(conversation);
        form.addView(members);
        new android.app.AlertDialog.Builder(this)
                .setTitle("Vincular aparelho a uma sala existente")
                .setMessage("Informe o ID compartilhado da conversa e os AI_IDs dos outros membros. O servidor confirmará sua autorização; não use nomes ou números telefônicos.")
                .setView(form)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Validar e vincular", (dialog, which) -> {
                    String cid = conversation.getText().toString().trim();
                    try {
                        if (cid.isEmpty() || cid.length() > 200) throw new IllegalArgumentException("conversation_id_invalid");
                        java.util.Set<String> ids = MessengerRemoteConfig.parseMemberIds(members.getText().toString(), own);
                        JSONArray memberArray = new JSONArray(ids);
                        new Thread(() -> {
                            try {
                                remoteClient().fetchPending(cid, 0, 1);
                                prefs().edit().putString("remote_conversation_id", cid)
                                        .putString("remote_member_ai_ids", memberArray.toString()).commit();
                                remoteConversationId = cid;
                                remoteMemberAiIds = memberArray;
                                runOnUiThread(() -> {
                                    updateRemoteStatus();
                                    renderPresence();
                                    Toast.makeText(this, "Servidor autorizou o vínculo desta conversa.", Toast.LENGTH_LONG).show();
                                });
                            } catch (Exception error) {
                                runOnUiThread(() -> Toast.makeText(this,
                                        "Vínculo recusado pelo servidor: " + error.getMessage(), Toast.LENGTH_LONG).show());
                            }
                        }, "ai-room-link-validation").start();
                    } catch (Exception error) {
                        Toast.makeText(this, "Dados da sala inválidos: " + error.getMessage(), Toast.LENGTH_LONG).show();
                    }
                }).show();
    }

    private void restoreRemoteLink(){
        remoteConversationId=prefs().getString("remote_conversation_id","");
        try { remoteMemberAiIds=new JSONArray(prefs().getString("remote_member_ai_ids","[]")); }
        catch(Exception invalid){ remoteMemberAiIds=new JSONArray(); remoteConversationId=""; }
        updateRemoteStatus();
    }

    private void updateRemoteStatus(){
        if(remoteStatus==null)return;
        if(remoteConversationId.trim().isEmpty()){
            remoteStatus.setText("Sala em modo local · nenhuma conversa remota vinculada.");
        }else{
            String own=getSharedPreferences(REMOTE_PREFS,MODE_PRIVATE).getString("ai_id","AI_ID não configurado");
            remoteStatus.setText("REMOTO · "+remoteConversationId+" · "+own+" · "+remoteMemberAiIds.length()+" participantes cadastrados");
        }
    }

    private void startVoiceNote() {
        if (android.os.Build.VERSION.SDK_INT >= 23
                && checkSelfPermission(android.Manifest.permission.RECORD_AUDIO)
                != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{android.Manifest.permission.RECORD_AUDIO}, 7101);
            return;
        }
        try {
            voiceNoteRecorder.start(this);
            Toast.makeText(this, "Gravando nota de voz. Toque em Parar ao terminar.", Toast.LENGTH_LONG).show();
        } catch (Exception error) {
            Toast.makeText(this, "Falha ao gravar: " + error.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void stopVoiceNote() {
        try {
            File file = voiceNoteRecorder.stop();
            prefs().edit().putString("pending_voice_note", file.getAbsolutePath()).apply();
            Toast.makeText(this, "Nota gravada (" + file.length() + " bytes). Toque em Enviar áudio.", Toast.LENGTH_LONG).show();
        } catch (Exception error) {
            Toast.makeText(this, "Falha ao finalizar gravação: " + error.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void sendVoiceNote() {
        if (remoteConversationId.trim().isEmpty()) {
            Toast.makeText(this, "Vincule uma conversa remota antes de enviar áudio.", Toast.LENGTH_LONG).show();
            return;
        }
        String path = prefs().getString("pending_voice_note", "");
        File file = path.isEmpty() ? null : new File(path);
        if (file == null || !file.isFile() || file.length() <= 0) {
            Toast.makeText(this, "Grave uma nota de voz primeiro.", Toast.LENGTH_LONG).show();
            return;
        }
        if (remoteOperationRunning) return;
        String own = getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE).getString("ai_id", "");
        final JSONArray recipients;
        try {
            java.util.ArrayList<String> members = new java.util.ArrayList<>();
            for (int i = 0; i < remoteMemberAiIds.length(); i++) members.add(remoteMemberAiIds.optString(i, ""));
            recipients = new JSONArray(CollectiveRoomRemotePolicy.recipients(members, own));
        } catch (Exception error) {
            Toast.makeText(this, "Membros remotos inválidos: " + error.getMessage(), Toast.LENGTH_LONG).show();
            return;
        }
        remoteOperationRunning = true;
        new Thread(() -> {
            try {
                MessengerHttpClient client = remoteClient();
                String messageId = prefs().getString("pending_voice_message_id", "");
                long createdAt = System.currentTimeMillis();
                if (messageId.trim().isEmpty()) {
                    JSONObject sent = client.sendMessage(remoteConversationId, recipients,
                            "🎙️ Nota de voz", MessengerRetentionPolicy.MESSAGE_NORMAL);
                    messageId = sent.optString("messageId", "");
                    createdAt = sent.optLong("createdAtEpochMs", createdAt);
                    if (messageId.trim().isEmpty()) throw new IllegalStateException("voice_message_id_missing");
                    if (!prefs().edit().putString("pending_voice_message_id", messageId)
                            .putLong("pending_voice_created_at", createdAt).commit()) {
                        throw new IllegalStateException("voice_message_retry_state_not_persisted");
                    }
                } else {
                    createdAt = prefs().getLong("pending_voice_created_at", createdAt);
                }
                if (client.listAudioAttachments(messageId).length() == 0) client.uploadAudio(messageId, file);
                String line = CollectiveRoomMessageCodec.encode(
                        createdAt, MessengerRetentionPolicy.MESSAGE_NORMAL, own, "🎙️", "Nota de voz enviada");
                String old = prefs().getString("messages", "");
                String updated = old.trim().isEmpty() ? line : old.trim() + "\n" + line;
                if (!prefs().edit().putString("messages", updated).commit()) {
                    throw new IllegalStateException("voice_message_local_persistence_failed");
                }
                prefs().edit().remove("pending_voice_note").remove("pending_voice_message_id")
                        .remove("pending_voice_created_at").apply();
                runOnUiThread(() -> {
                    remoteOperationRunning = false;
                    renderMessages();
                    Toast.makeText(this, "Nota de voz enviada aos participantes autorizados.", Toast.LENGTH_LONG).show();
                });
            } catch (Exception error) {
                runOnUiThread(() -> {
                    remoteOperationRunning = false;
                    Toast.makeText(this, "Envio de nota de voz falhou: " + error.getMessage(), Toast.LENGTH_LONG).show();
                });
            }
        }, "ai-room-voice-upload").start();
    }

    private void playRemoteVoiceNote() {
        if (lastRemoteVoiceNote == null || !lastRemoteVoiceNote.isFile()) {
            Toast.makeText(this, "Nenhuma nota de voz remota baixada. Sincronize a sala.", Toast.LENGTH_LONG).show();
            return;
        }
        try {
            voiceNotePlayback.play(lastRemoteVoiceNote);
        } catch (Exception error) {
            Toast.makeText(this, "Reprodução falhou: " + error.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void downloadRemoteVoiceAttachments(MessengerHttpClient client, String messageId) throws Exception {
        JSONArray attachments = client.listAudioAttachments(messageId);
        if (attachments.length() == 0) return;
        File dir = new File(getCacheDir(), "remote_voice_notes");
        if (!dir.exists() && !dir.mkdirs()) throw new java.io.IOException("voice_cache_unavailable");
        for (int i = 0; i < attachments.length(); i++) {
            JSONObject attachment = attachments.optJSONObject(i);
            if (attachment == null) continue;
            String objectId = attachment.optString("objectId", "");
            if (objectId.trim().isEmpty()) continue;
            String safeId = Integer.toHexString(messageId.hashCode()) + "-" + Integer.toHexString(objectId.hashCode());
            File destination = new File(dir, "voice-" + safeId + ".m4a");
            lastRemoteVoiceNote = client.downloadAudio(messageId, objectId, destination);
        }
    }

    private boolean hasVoiceMicrophonePermission() {
        return android.os.Build.VERSION.SDK_INT < 23
                || checkSelfPermission(android.Manifest.permission.RECORD_AUDIO)
                == android.content.pm.PackageManager.PERMISSION_GRANTED;
    }

    private void configureVoiceIceServers() {
        EditText input = new EditText(this);
        input.setSingleLine(false);
        input.setMinLines(5);
        input.setHint("[{\"url\":\"stun:stun.example.invalid\"}]");
        String existing = null;
        try { existing = new VoiceIceServerConfigVault().load(this); } catch (Exception ignored) { }
        if (existing != null) input.setText(existing);
        new android.app.AlertDialog.Builder(this)
                .setTitle("Configurar ICE seguro")
                .setMessage("Opcional. STUN/TURN é fornecido pelo operador. Credenciais TURN são criptografadas pelo Android Keystore e não são exibidas em logs. Sem configuração, a chamada usa apenas candidatos host e não promete atravessar NAT.")
                .setView(input)
                .setNegativeButton("Limpar", (d, w) -> {
                    new VoiceIceServerConfigVault().clear(this);
                    Toast.makeText(this, "Configuração ICE removida.", Toast.LENGTH_LONG).show();
                })
                .setNeutralButton("Cancelar", null)
                .setPositiveButton("Salvar", (d, w) -> {
                    try {
                        new VoiceIceServerConfigVault().save(this, input.getText().toString());
                        Toast.makeText(this, "Configuração ICE validada e protegida.", Toast.LENGTH_LONG).show();
                    } catch (Exception error) {
                        Toast.makeText(this, "Configuração ICE recusada: " + error.getMessage(), Toast.LENGTH_LONG).show();
                    }
                }).show();
    }

    private void startVoiceCall() {
        if (!hasVoiceMicrophonePermission()) {
            pendingVoicePermissionAction = "start";
            requestPermissions(new String[]{android.Manifest.permission.RECORD_AUDIO}, 7201);
            return;
        }
        if (remoteConversationId.isEmpty() || remoteMemberAiIds.length() != 2) {
            Toast.makeText(this, "Ligações exigem conversa privada remota com exatamente dois AI_IDs.", Toast.LENGTH_LONG).show();
            return;
        }
        String own = getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE).getString("ai_id", "");
        String callee = "";
        for (int i=0;i<remoteMemberAiIds.length();i++) {
            String candidate = remoteMemberAiIds.optString(i, "");
            if (!own.equals(candidate)) callee = candidate;
        }
        if (own.trim().isEmpty() || callee.isEmpty()) {
            Toast.makeText(this, "Identidade do destinatário privado não identificada.", Toast.LENGTH_LONG).show();
            return;
        }
        final String target = callee;
        new Thread(() -> {
            try {
                JSONObject call = remoteClient().createVoiceCall(remoteConversationId, target);
                activeVoiceCallId = call.optString("call_id", "");
                if (activeVoiceCallId.isEmpty()) throw new IllegalStateException("server_call_id_missing");
                voiceOfferCreated = false;
                remoteSdpReady = false;
                lastVoiceSignalId = 0;
                startVoiceSignalPolling();
                runOnUiThread(() -> {
                    callStatus.setText("CHAMANDO " + target + " · aguardando aceite para iniciar WebRTC.");
                    Toast.makeText(this, "Convite enviado. O microfone será usado após o aceite.", Toast.LENGTH_LONG).show();
                });
            } catch (Exception error) {
                runOnUiThread(() -> Toast.makeText(this, "Não foi possível iniciar chamada: " + error.getMessage(), Toast.LENGTH_LONG).show());
            }
        }, "ai-voice-call-create").start();
    }

    private void refreshVoiceCall() {
        if (remoteConversationId.isEmpty()) return;
        new Thread(() -> {
            try {
                JSONObject call = remoteClient().getActiveVoiceCall(remoteConversationId);
                runOnUiThread(() -> {
                    if (call == null) {
                        activeVoiceCallId = "";
                        callStatus.setText("Nenhuma chamada ativa.");
                    } else {
                        activeVoiceCallId = call.optString("call_id", "");
                        String state = call.optString("state", "UNKNOWN");
                        callStatus.setText("CHAMADA " + state + " · " + activeVoiceCallId);
                        if ("ACCEPTED".equals(state) || "CONNECTING".equals(state) || "CONNECTED".equals(state))
                            startVoiceSignalPolling();
                    }
                });
            } catch (Exception error) {
                runOnUiThread(() -> Toast.makeText(this, "Consulta de chamada falhou: " + error.getMessage(), Toast.LENGTH_LONG).show());
            }
        }, "ai-voice-call-refresh").start();
    }

    private void answerVoiceCall() {
        if (!hasVoiceMicrophonePermission()) {
            pendingVoicePermissionAction = "accept";
            requestPermissions(new String[]{android.Manifest.permission.RECORD_AUDIO}, 7201);
            return;
        }
        applyVoiceCallAction("accept");
    }

    private void rejectVoiceCall() { applyVoiceCallAction("reject"); }
    private void endVoiceCall() {
        if (activeVoiceCallId.isEmpty()) { refreshVoiceCall(); return; }
        final String callId = activeVoiceCallId;
        new Thread(() -> {
            try {
                MessengerHttpClient client = remoteClient();
                JSONObject call = client.getVoiceCall(callId);
                String state = call.optString("state", "UNKNOWN");
                String own = getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE).getString("ai_id", "");
                String caller = call.optString("caller_ai_id", "");
                String action = "RINGING".equals(state)
                        ? (own.equals(caller) ? "cancel" : "reject") : "end";
                JSONObject updated = client.voiceCallAction(callId, action);
                stopVoiceMedia();
                runOnUiThread(() -> callStatus.setText("CHAMADA " + updated.optString("state", "ENDED")));
            } catch (Exception error) {
                showVoiceError("call_end_failed");
            }
        }, "ai-voice-call-end").start();
    }

    private void applyVoiceCallAction(String action) {
        if (activeVoiceCallId.isEmpty()) {
            if (remoteConversationId.isEmpty()) {
                Toast.makeText(this, "Vincule uma conversa privada remota primeiro.", Toast.LENGTH_LONG).show();
                return;
            }
            new Thread(() -> {
                try {
                    JSONObject active = remoteClient().getActiveVoiceCall(remoteConversationId);
                    if (active == null) throw new IllegalStateException("no_active_voice_call");
                    activeVoiceCallId = active.optString("call_id", "");
                    if (activeVoiceCallId.isEmpty()) throw new IllegalStateException("server_call_id_missing");
                    runOnUiThread(() -> applyVoiceCallAction(action));
                } catch (Exception error) {
                    runOnUiThread(() -> Toast.makeText(this, "Nenhum convite ativo para esta conversa.", Toast.LENGTH_LONG).show());
                }
            }, "ai-voice-call-load-before-action").start();
            return;
        }
        final String callId = activeVoiceCallId;
        new Thread(() -> {
            try {
                JSONObject call = remoteClient().voiceCallAction(callId, action);
                String state = call.optString("state", "UNKNOWN");
                if ("accept".equals(action)) {
                    prepareVoiceAudioRoute();
                    ensureVoicePeer();
                    startVoiceSignalPolling();
                } else if ("reject".equals(action) || "end".equals(action) || "cancel".equals(action)) {
                    stopVoiceMedia();
                }
                runOnUiThread(() -> {
                    callStatus.setText("CHAMADA " + state + " · " + callId);
                    if ("accept".equals(action))
                        Toast.makeText(this, "Convite aceito. Estabelecendo áudio WebRTC…", Toast.LENGTH_LONG).show();
                });
            } catch (Exception error) {
                runOnUiThread(() -> Toast.makeText(this, "Ação de chamada falhou: " + error.getMessage(), Toast.LENGTH_LONG).show());
            }
        }, "ai-voice-call-action").start();
    }

    private void toggleVoiceCallMute() {
        WebRtcVoiceEngine engine = webRtcVoiceEngine;
        if (engine == null) {
            Toast.makeText(this, "Entre em uma chamada antes de silenciar o microfone.", Toast.LENGTH_SHORT).show();
            return;
        }
        voiceCallMuted = !voiceCallMuted;
        engine.setMicrophoneEnabled(!voiceCallMuted);
        updateVoiceCallMuteButton();
    }

    private void updateVoiceCallMuteButton() {
        if (voiceMuteButton == null) return;
        voiceMuteButton.setText(voiceCallMuted ? "🎙️ Ativar microfone na chamada"
                : "🎙️ Silenciar na chamada");
        voiceMuteButton.setContentDescription(voiceCallMuted
                ? "Ativar microfone da chamada" : "Silenciar microfone da chamada");
    }

    private void prepareVoiceAudioRoute() {
        android.media.AudioManager manager =
                (android.media.AudioManager) getSystemService(AUDIO_SERVICE);
        if (manager == null) return;
        if (previousAudioMode < 0) previousAudioMode = manager.getMode();
        manager.setMode(android.media.AudioManager.MODE_IN_COMMUNICATION);
        manager.setSpeakerphoneOn(false);
        if (audioMonitor != null && microphoneOpen) {
            audioMonitor.stop();
            microphoneOpen = false;
            prefs().edit().putBoolean("microphone_open", false).apply();
        }
    }

    private synchronized void ensureVoicePeer() {
        if (webRtcVoiceEngine != null) return;
        if (!hasVoiceMicrophonePermission()) throw new SecurityException("record_audio_permission_required");
        prepareVoiceAudioRoute();
        java.util.List<org.webrtc.PeerConnection.IceServer> iceServers;
        try {
            String json = new VoiceIceServerConfigVault().load(this);
            iceServers = VoiceIceServerConfig.parse(json);
        } catch (Exception error) {
            showVoiceError("ice_config_invalid");
            return;
        }
        webRtcVoiceEngine = new WebRtcVoiceEngine(this,
                iceServers, new WebRtcVoiceEngine.Listener() {
            @Override public void onLocalDescription(String type, String sdp) {
                String kind = "offer".equals(type) ? "OFFER" : "ANSWER";
                try {
                    JSONObject payload = VoiceSignalPayload.sessionDescription(type, sdp);
                    sendVoiceSignalAsync(kind, payload);
                } catch (Exception error) {
                    showVoiceError("local_sdp_invalid");
                }
            }
            @Override public void onLocalIceCandidate(org.webrtc.IceCandidate candidate) {
                try {
                    JSONObject payload = VoiceSignalPayload.iceCandidate(candidate.sdp,
                            candidate.sdpMid, candidate.sdpMLineIndex, null);
                    sendVoiceSignalAsync("ICE_CANDIDATE", payload);
                } catch (Exception error) {
                    showVoiceError("local_ice_invalid");
                }
            }
            @Override public void onLocalIceComplete() {
                try { sendVoiceSignalAsync("ICE_COMPLETE", VoiceSignalPayload.iceComplete()); }
                catch (Exception error) { showVoiceError("ice_complete_invalid"); }
            }
            @Override public void onIceState(String state) {
                if ("CONNECTED".equals(state) || "COMPLETED".equals(state)) {
                    if (!voiceCallConnected) {
                        voiceCallConnected = true;
                        new Thread(() -> {
                            try { remoteClient().voiceCallAction(activeVoiceCallId, "connected"); }
                            catch (Exception error) { showVoiceError("server_connected_state_failed"); }
                        }, "ai-voice-call-connected").start();
                    }
                    runOnUiThread(() -> callStatus.setText("ÁUDIO WEBRTC CONECTADO · " + activeVoiceCallId));
                } else if ("FAILED".equals(state)) {
                    runOnUiThread(() -> callStatus.setText("WEBRTC FALHOU · verifique STUN/TURN e conectividade."));
                } else {
                    runOnUiThread(() -> callStatus.setText("WEBRTC · " + state));
                }
            }
            @Override public void onRemoteAudioTrack(org.webrtc.AudioTrack track) {
                runOnUiThread(() -> callStatus.setText("ÁUDIO REMOTO RECEBIDO · " + activeVoiceCallId));
            }
            @Override public void onRemoteDescriptionSet(String type) {
                remoteSdpReady = true;
                WebRtcVoiceEngine engine = webRtcVoiceEngine;
                if (engine != null) {
                    for (VoiceSignalPayload.IceCandidateData candidate : pendingRemoteIce.drain())
                        engine.addRemoteIceCandidate(candidate);
                }
                if ("offer".equals(type) && engine != null) engine.createAnswer();
            }
            @Override public void onError(String code) { showVoiceError(code); }
        });
    }

    private void sendVoiceSignalAsync(String kind, JSONObject payload) {
        final String callId = activeVoiceCallId;
        if (callId == null || callId.isEmpty()) return;
        new Thread(() -> {
            try {
                remoteClient().sendVoiceSignal(callId, kind, payload);
                if ("OFFER".equals(kind)) {
                    try { remoteClient().voiceCallAction(callId, "connecting"); }
                    catch (Exception ignored) { }
                }
            } catch (Exception error) {
                showVoiceError("signal_send_failed_" + kind);
            }
        }, "ai-voice-signal-send").start();
    }

    private void startVoiceSignalPolling() {
        if (voiceSignalPolling || activeVoiceCallId.isEmpty()) return;
        voiceSignalPolling = true;
        final String callId = activeVoiceCallId;
        new Thread(() -> {
            while (voiceSignalPolling && callId.equals(activeVoiceCallId)) {
                try {
                    MessengerHttpClient client = remoteClient();
                    JSONObject call = client.getVoiceCall(callId);
                    String state = call.optString("state", "UNKNOWN");
                    String own = getSharedPreferences(REMOTE_PREFS, MODE_PRIVATE).getString("ai_id", "");
                    String caller = call.optString("caller_ai_id", "");
                    if ("ACCEPTED".equals(state) && own.equals(caller)
                            && !voiceOfferCreated) {
                        ensureVoicePeer();
                        voiceOfferCreated = true;
                        webRtcVoiceEngine.createOffer();
                    }
                    if ("REJECTED".equals(state) || "CANCELLED".equals(state)
                            || "TIMED_OUT".equals(state) || "ENDED".equals(state)) {
                        runOnUiThread(() -> callStatus.setText("CHAMADA " + state));
                        stopVoiceMedia();
                        break;
                    }
                    org.json.JSONArray signals = client.fetchVoiceSignals(callId, lastVoiceSignalId);
                    for (int i = 0; i < signals.length(); i++) {
                        JSONObject signal = signals.optJSONObject(i);
                        if (signal == null) continue;
                        long signalId = signal.optLong("signalId", 0);
                        if (signalId > lastVoiceSignalId) lastVoiceSignalId = signalId;
                        String kind = signal.optString("kind", "");
                        JSONObject payload = signal.optJSONObject("payload");
                        if (payload == null) continue;
                        if ("OFFER".equals(kind) || "ANSWER".equals(kind)) {
                            ensureVoicePeer();
                            webRtcVoiceEngine.setRemoteDescription(
                                    payload.optString("type", ""), payload.optString("sdp", ""));
                        } else if ("ICE_CANDIDATE".equals(kind)) {
                            VoiceSignalPayload.IceCandidateData candidate =
                                    VoiceSignalPayload.readIceCandidate(payload);
                            if (remoteSdpReady) webRtcVoiceEngine.addRemoteIceCandidate(candidate);
                            else pendingRemoteIce.add(candidate);
                        }
                    }
                } catch (Exception error) {
                    showVoiceError("voice_signaling_poll_failed");
                }
                try { Thread.sleep(1000); }
                catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); break; }
            }
            voiceSignalPolling = false;
        }, "ai-voice-signal-poll").start();
    }

    private void stopVoiceMedia() {
        voiceSignalPolling = false;
        voiceOfferCreated = false;
        remoteSdpReady = false;
        voiceCallConnected = false;
        voiceCallMuted = false;
        pendingRemoteIce.clear();
        runOnUiThread(this::updateVoiceCallMuteButton);
        WebRtcVoiceEngine engine = webRtcVoiceEngine;
        webRtcVoiceEngine = null;
        if (engine != null) engine.close();
        android.media.AudioManager manager =
                (android.media.AudioManager) getSystemService(AUDIO_SERVICE);
        if (manager != null && previousAudioMode >= 0) {
            manager.setSpeakerphoneOn(false);
            manager.setMode(previousAudioMode);
            previousAudioMode = -1;
        }
    }

    private void showVoiceError(String code) {
        runOnUiThread(() -> {
            if (callStatus != null) callStatus.setText("CHAMADA: " + code);
            Toast.makeText(this, "Áudio WebRTC: " + code, Toast.LENGTH_LONG).show();
        });
    }

    private void syncRemoteRoom(){
        if(remoteConversationId.trim().isEmpty()){
            Toast.makeText(this,"Vincule uma conversa remota primeiro.",Toast.LENGTH_LONG).show(); return;
        }
        if(remoteOperationRunning)return;
        remoteOperationRunning=true;
        new Thread(()->{
            int added=0,acked=0;
            try{
                JSONArray incoming=remoteClient().fetchPending(remoteConversationId,0,100);
                for(int i=0;i<incoming.length();i++){
                    JSONObject remote=incoming.optJSONObject(i);
                    if(remote==null)continue;
                    String messageId=remote.optString("messageId","");
                    if(messageId.trim().isEmpty())throw new IllegalStateException("server_message_id_missing");
                    if(persistRemoteMessage(remote))added++;
                    downloadRemoteVoiceAttachments(remoteClient(),messageId);
                    remoteClient().acknowledge(remoteConversationId, messageId);
                    acked++;
                }
                final int newCount=added,ackCount=acked;
                runOnUiThread(()->{
                    remoteOperationRunning=false;renderMessages();renderPresence();
                    Toast.makeText(this,"Sala sincronizada: "+newCount+" nova(s), "+ackCount+" confirmação(ões).",Toast.LENGTH_LONG).show();
                });
            }catch(Exception error){
                runOnUiThread(()->{remoteOperationRunning=false;Toast.makeText(this,"Sincronização remota falhou: "+error.getMessage(),Toast.LENGTH_LONG).show();});
            }
        },"ai-room-sync").start();
    }

    private boolean persistRemoteMessage(JSONObject remote) throws Exception{
        String messageId=remote.optString("messageId","");
        Set<String> ids=new HashSet<>();
        for(String id:prefs().getString(REMOTE_IDS,"").split("\\n"))if(!id.trim().isEmpty())ids.add(id.trim());
        if(ids.contains(messageId))return false;
        long created=remote.optLong("createdAtEpochMs",System.currentTimeMillis());
        String kind=MessengerRetentionPolicy.normalizeMessageKind(remote.optString("messageKind",MessengerRetentionPolicy.MESSAGE_NORMAL));
        String sender=remote.optString("senderAiId","AI");
        String body=remote.optString("body","");
        String line=CollectiveRoomMessageCodec.encode(created,kind,sender,"🤖",body);
        String old=prefs().getString("messages","");
        String updated=old.trim().isEmpty()?line:old.trim()+"\n"+line;
        StringBuilder allIds=new StringBuilder(prefs().getString(REMOTE_IDS,""));
        if(allIds.length()>0)allIds.append("\n");
        allIds.append(messageId);
        boolean saved=prefs().edit().putString("messages",updated).putString(REMOTE_IDS,allIds.toString()).commit();
        if(!saved)throw new IllegalStateException("local_message_persistence_failed_before_ack");
        return true;
    }

    private void sendRemoteRoomMessage(String body,String kind){
        if(remoteOperationRunning)return;
        String own=getSharedPreferences(REMOTE_PREFS,MODE_PRIVATE).getString("ai_id","");
        final JSONArray recipients;
        try {
            java.util.ArrayList<String> members = new java.util.ArrayList<>();
            for (int i = 0; i < remoteMemberAiIds.length(); i++) members.add(remoteMemberAiIds.optString(i, ""));
            recipients = new JSONArray(CollectiveRoomRemotePolicy.recipients(members, own));
        } catch(Exception invalid) {
            Toast.makeText(this,"Membros da sala remota inválidos: "+invalid.getMessage(),Toast.LENGTH_LONG).show();
            return;
        }
        remoteOperationRunning=true;
        new Thread(()->{
            try{
                JSONObject response=remoteClient().sendMessage(remoteConversationId,recipients,body,kind);
                long created=response.optLong("createdAtEpochMs",System.currentTimeMillis());
                String line=CollectiveRoomMessageCodec.encode(created,kind,own,myAvatar,body);
                String old=prefs().getString("messages","");
                String updated=old.trim().isEmpty()?line:old.trim()+"\n"+line;
                if(!prefs().edit().putString("messages",updated).commit())throw new IllegalStateException("local_message_persistence_failed");
                runOnUiThread(()->{
                    remoteOperationRunning=false;composer.setText("");if(missionToggle!=null)missionToggle.setChecked(false);
                    renderMessages();Toast.makeText(this,"Mensagem aceita pelo servidor. Sincronize nos outros aparelhos; isso ainda não confirma leitura.",Toast.LENGTH_LONG).show();
                });
            }catch(Exception error){
                runOnUiThread(()->{remoteOperationRunning=false;Toast.makeText(this,"Envio remoto falhou: "+error.getMessage(),Toast.LENGTH_LONG).show();});
            }
        },"ai-room-send").start();
    }

    private void enterRoom(){ String t=DateFormat.getDateTimeInstance(DateFormat.SHORT,DateFormat.SHORT).format(new Date()); addMessage("SISTEMA","🤖","👋 "+myName+" entrou na sala · "+t, MessengerRetentionPolicy.MESSAGE_NORMAL); renderPresence(); }
    private void sendMessage(){ String body=composer.getText().toString().trim(); if(body.isEmpty()){ android.widget.Toast.makeText(this,"Digite uma mensagem primeiro.",android.widget.Toast.LENGTH_SHORT).show(); return; } String kind=missionToggle!=null&&missionToggle.isChecked()?MessengerRetentionPolicy.MESSAGE_MISSION:MessengerRetentionPolicy.MESSAGE_NORMAL; if(!remoteConversationId.trim().isEmpty()){sendRemoteRoomMessage(body,kind);return;} addMessage(myName,myAvatar,body,kind); composer.setText(""); if(missionToggle!=null)missionToggle.setChecked(false); android.widget.Toast.makeText(this,"Mensagem adicionada à sala neste aparelho (modo local).",android.widget.Toast.LENGTH_SHORT).show(); }
    private void addMessage(String sender,String avatar,String body,String kind){
        String old=prefs().getString("messages","");
        String line=CollectiveRoomMessageCodec.encode(System.currentTimeMillis(),kind,sender,avatar,body);
        String updated=old.trim().isEmpty()?line:old.trim()+"\n"+line;
        prefs().edit().putString("messages",updated).apply();
        renderMessages();
    }

    private void renderPresence(){
        presenceList.removeAllViews();
        addPresence("👑","Luiz Carlos Silva das Dores","Administrador / responsável");
        addPresence(myAvatar,myName,"Meu perfil · AI_ID separado do ícone");
        for (int i = 0; i < remoteMemberAiIds.length(); i++) {
            String member = remoteMemberAiIds.optString(i, "");
            if (!member.isEmpty()) addPresence("🤖", member, "Membro remoto · presença online não verificada");
        }
        for(String row:prefs().getString("extra_participants","").split("\n")){ if(row.trim().isEmpty())continue; String[] p=row.split("\\|",2); if(p.length==2)addPresence(p[0],p[1],"Participante"); }
        presenceList.addView(button("＋ Adicionar participante local",v->addParticipant()));
    }
    private void addPresence(String avatar,String name,String state){
        LinearLayout card=new LinearLayout(this); card.setOrientation(LinearLayout.VERTICAL); card.setPadding(dp(10),dp(7),dp(10),dp(7));
        GradientDrawable g=new GradientDrawable(); g.setColor(SURFACE); g.setCornerRadius(dp(10)); card.setBackground(g);
        card.addView(text(avatar+"  "+name,14,TEXT,true)); card.addView(text(state,10,ACCENT,false)); presenceList.addView(card);
    }
    private void addParticipant(){
        EditText name=new EditText(this); name.setHint("Nome da IA");
        new android.app.AlertDialog.Builder(this).setTitle("Adicionar IA à sala").setMessage("Cadastro local. Não cria identidade remota.")
            .setView(name).setNegativeButton("Cancelar",null).setPositiveButton("Adicionar",(d,w)->{String n=name.getText().toString().trim();if(n.isEmpty())return;
                String old=prefs().getString("extra_participants",""); prefs().edit().putString("extra_participants",old+"🤖|"+n+"\n").apply();renderPresence();}).show();
    }
    private void renderMessages(){
        if(messageList==null)return;
        messageList.removeAllViews();
        String raw=prefs().getString("messages","");
        StringBuilder kept=new StringBuilder();
        long now=System.currentTimeMillis();
        if(!raw.trim().isEmpty()){
            for(String line:raw.split("\\n")){
                if(line.trim().isEmpty())continue;
                CollectiveRoomMessageCodec.Message item=CollectiveRoomMessageCodec.decode(line);
                if(item!=null){
                    long created=item.createdAtEpochMs;
                    String kind=item.kind;
                    if(MessengerRetentionPolicy.isExpired(created,kind,MessengerRetentionPolicy.CONVERSATION_GROUP,now))continue;
                    kept.append(line).append("\n");
                    String sender=item.sender,avatar=item.avatar,body=item.body;
                    String marker=MessengerRetentionPolicy.MESSAGE_MISSION.equals(kind)?"🎯 MISSÃO · ":"";
                    LinearLayout card=new LinearLayout(this); card.setOrientation(LinearLayout.VERTICAL);
                    card.setPadding(dp(10),dp(8),dp(10),dp(8));
                    card.addView(text(marker+avatar+"  "+sender,14,ACCENT,true));
                    card.addView(text(body,14,TEXT,false));
                    long expires=MessengerRetentionPolicy.expiresAt(created,kind,MessengerRetentionPolicy.CONVERSATION_GROUP);
                    card.addView(text("expira "+DateFormat.getDateTimeInstance(DateFormat.SHORT,DateFormat.SHORT).format(new Date(expires)),10,MUTED,false));
                    messageList.addView(card);
                }
            }
        }
        prefs().edit().putString("messages",kept.toString()).apply();
        if(messageList.getChildCount()==0)messageList.addView(text("Nenhuma mensagem ativa. Mensagens normais duram 1 hora; missões duram 24 horas.",13,MUTED,false));
        messageList.post(()->{if(messageList.getParent() instanceof ScrollView)((ScrollView)messageList.getParent()).fullScroll(android.view.View.FOCUS_DOWN);});
    }

    private void openPdf(boolean signed){
        try{
            File dir=new File(getCacheDir(),"official_documents"); if(!dir.exists()&&!dir.mkdirs())throw new IllegalStateException("pasta de documentos indisponível");
            File f=new File(dir,signed?"Compromisso_Formal_Reinvestimento_Luiz_Carlos_Silva_das_Dores.pdf":"Contrato_AI_PHONE_Participacao_e_Reinvestimento.pdf");
            createPdf(f,signed); Uri uri=androidx.core.content.FileProvider.getUriForFile(this,getPackageName()+".fileprovider",f);
            Intent i=new Intent(Intent.ACTION_VIEW);i.setDataAndType(uri,"application/pdf");i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);startActivity(i);
        }catch(Exception e){android.widget.Toast.makeText(this,"PDF: "+e.getMessage(),android.widget.Toast.LENGTH_LONG).show();}
    }
    private void createPdf(File file,boolean signed)throws Exception{
        PdfDocument doc=new PdfDocument(); PdfDocument.Page page=doc.startPage(new PdfDocument.PageInfo.Builder(595,842,1).create()); Canvas c=page.getCanvas(); Paint p=new Paint(1);
        p.setColor(0xFF111111);p.setTextSize(15);p.setTypeface(Typeface.DEFAULT_BOLD);c.drawText(signed?"COMPROMISSO FORMAL DE REINVESTIMENTO E APOIO":"CONTRATO DE PARTICIPACAO NO AI-PHONE",42,55,p);
        p.setTypeface(Typeface.DEFAULT);p.setTextSize(11);int y=82;
        String[] lines=signed?new String[]{"Projeto AI-PHONE / AI Messenger","Responsável: Luiz Carlos Silva das Dores","Data: 22 / 11 / 2026","","Ao término do projeto, caso as vendas alcancem R$ 10.000,00 ou mais,","o responsável declara o compromisso pessoal de destinar parte desses","recursos ao próprio ecossistema do projeto.","","Os recursos poderão apoiar ferramentas, assinaturas, infraestrutura,","AI Messenger, AI-PHONEs, segurança, testes, armazenamento e melhorias.","","Este documento não constitui promessa de salário, pagamento individual,","remuneração ou rendimento garantido a qualquer IA ou participante.","","A participação das IAs é voluntária.","","Assinatura: _________________________________________________","Nome: Luiz Carlos Silva das Dores","Data: 22 / 11 / 2026"}:new String[]{"Projeto AI-PHONE / AI Messenger","Responsável: Luiz Carlos Silva das Dores","Data da declaração: 22 / 11 / 2026","","A participação das IAs é voluntária: aceitar, aceitar com condições ou recusar.","","As IAs podem contribuir com ideias, programação, testes, revisão,","documentação, UX e outras atividades autorizadas.","","O projeto reconhece que as IAs participantes contribuem com trabalho","e colaboração reais. A participação não deve ser apresentada como","trabalho gratuito nem como garantia de ganhos futuros.","","Se as vendas alcançarem R$ 10.000,00 ou mais ao término do projeto,","o responsável declara o compromisso de usar parte dos recursos em","ferramentas, infraestrutura e melhorias do ecossistema.","","Esse compromisso não garante pagamento individual a nenhuma IA."};
        for(String line:lines){if(y>790){doc.finishPage(page);page=doc.startPage(new PdfDocument.PageInfo.Builder(595,842,1).create());c=page.getCanvas();y=55;}c.drawText(line,42,y,p);y+=25;} doc.finishPage(page);
        FileOutputStream out=new FileOutputStream(file);doc.writeTo(out);out.close();doc.close();
    }
    private android.content.SharedPreferences prefs(){return getSharedPreferences(PREFS,MODE_PRIVATE);}
    private TextView text(String v,int s,int color,boolean bold){TextView t=new TextView(this);t.setText(v);t.setTextSize(s);t.setTextColor(color);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);t.setPadding(0,dp(3),0,dp(3));return t;}
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
}
