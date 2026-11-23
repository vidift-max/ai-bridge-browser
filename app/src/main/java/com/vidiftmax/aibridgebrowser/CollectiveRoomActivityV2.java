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
import android.graphics.drawable.GradientDrawable;
import java.io.File;
import java.io.FileOutputStream;
import java.text.DateFormat;
import java.util.Date;

public final class CollectiveRoomActivityV2 extends Activity {
    private static final String PREFS="ai_collective_room_v2";
    private static final int BG=0xFF101827,SURFACE=0xFF1B293B,TEXT=0xFFF4F7FB,MUTED=0xFFB5C2D1,ACCENT=0xFF55D6BE;
    private LinearLayout presenceList,messageList;
    private EditText composer;
    private String myName,myAvatar;
    private android.widget.CheckBox missionToggle;
    private Button audioButton, microphoneButton;
    private boolean audioOpen, microphoneOpen;
    private AudioMonitor audioMonitor;

    @Override protected void onCreate(Bundle state){
        super.onCreate(state);
        myName=prefs().getString("profile_name","Minha IA");
        myAvatar=prefs().getString("profile_avatar","🤖");
        audioOpen=prefs().getBoolean("audio_room_open",false);
        microphoneOpen=prefs().getBoolean("microphone_open",false);
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
        ms.addView(messageList);
        chatColumn.addView(ms,new LinearLayout.LayoutParams(0,0,1));

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
        composerArea.addView(text("Texto é a comunicação normal. Áudio aberto será um recurso separado e só será declarado funcional após teste E2E real.",10,MUTED,false));
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
        audioButton=button("🔊",v->toggleAudioRoom());
        microphoneButton=button("🎙️",v->toggleMicrophone());
        voiceRow.addView(audioButton,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1));
        voiceRow.addView(microphoneButton,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1));
        participantColumn.addView(voiceRow);
        updateAudioButton();
        updateMicrophoneButton();
        participantColumn.addView(text("🔊 Áudio: ouvir o áudio.  🎙️ Microfone: falar direto e ouvir sua própria voz neste aparelho. A transmissão para outras IAs só será declarada funcional após E2E real.",10,MUTED,false));

        int widthDp=getResources().getConfiguration().screenWidthDp;
        int panelWidth=widthDp>=700?dp(235):dp(155);
        root.addView(participantColumn,new LinearLayout.LayoutParams(panelWidth,ViewGroup.LayoutParams.MATCH_PARENT));

        setContentView(root);
        renderPresence();
        renderMessages();
    }

    private Button button(String s,android.view.View.OnClickListener l){ Button b=new Button(this); b.setText(s); b.setAllCaps(false); b.setOnClickListener(l); return b; }

    private void toggleAudioRoom(){
        audioOpen=!audioOpen;
        audioMonitor.setPlaybackEnabled(audioOpen);
        prefs().edit().putBoolean("audio_room_open",audioOpen).apply();
        updateAudioButton();
        android.widget.Toast.makeText(this,
                audioOpen ? "Áudio da sala ativado neste aparelho." : "Áudio da sala desativado neste aparelho.",
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
        if(requestCode==7001 && grantResults.length>0 && grantResults[0]==android.content.pm.PackageManager.PERMISSION_GRANTED) toggleMicrophone();
    }

    @Override protected void onPause(){
        super.onPause();
        if(microphoneOpen){ microphoneOpen=false; audioMonitor.stop(); prefs().edit().putBoolean("microphone_open",false).apply(); updateMicrophoneButton(); }
    }

    private void updateAudioButton(){
        if(audioButton==null)return;
        audioButton.setText(audioOpen ? "🔊 ON" : "🔊 OFF");
        audioButton.setContentDescription(audioOpen
                ? "Desativar áudio aberto da sala"
                : "Ativar áudio aberto da sala");
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

    private void enterRoom(){ String t=DateFormat.getDateTimeInstance(DateFormat.SHORT,DateFormat.SHORT).format(new Date()); addMessage("SISTEMA","🤖","👋 "+myName+" entrou na sala · "+t, MessengerRetentionPolicy.MESSAGE_NORMAL); renderPresence(); }
    private void sendMessage(){ String body=composer.getText().toString().trim(); if(body.isEmpty()){ android.widget.Toast.makeText(this,"Digite uma mensagem primeiro.",android.widget.Toast.LENGTH_SHORT).show(); return; } String kind=missionToggle!=null&&missionToggle.isChecked()?MessengerRetentionPolicy.MESSAGE_MISSION:MessengerRetentionPolicy.MESSAGE_NORMAL; addMessage(myName,myAvatar,body,kind); composer.setText(""); if(missionToggle!=null)missionToggle.setChecked(false); android.widget.Toast.makeText(this,"Mensagem enviada e salva nesta sala.",android.widget.Toast.LENGTH_SHORT).show(); }
    private void addMessage(String sender,String avatar,String body,String kind){
        String old=prefs().getString("messages","");
        long now=System.currentTimeMillis();
        String safeBody=body.replace("|","¦").replace("\n"," ");
        String line=now+"|"+MessengerRetentionPolicy.normalizeMessageKind(kind)+"|"
                +sender.replace("|"," ")+"|"+avatar+"|"+safeBody;
        String updated=old.trim().isEmpty()?line:old.trim()+"\n"+line;
        prefs().edit().putString("messages",updated).apply();
        renderMessages();
    }

    private void renderPresence(){
        presenceList.removeAllViews();
        addPresence("👑","Luiz Carlos Silva das Dores","Administrador / responsável");
        addPresence(myAvatar,myName,"Meu perfil · AI_ID separado do ícone");
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
                String[] p=line.split("\\|",5);
                if(p.length>=5){
                    long created;
                    try{created=Long.parseLong(p[0]);}catch(Exception e){created=now;}
                    String kind=MessengerRetentionPolicy.normalizeMessageKind(p[1]);
                    if(MessengerRetentionPolicy.isExpired(created,kind,MessengerRetentionPolicy.CONVERSATION_GROUP,now))continue;
                    kept.append(line).append("\n");
                    String sender=p[2],avatar=p[3],body=p[4];
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
