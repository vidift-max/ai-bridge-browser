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

    @Override protected void onCreate(Bundle state){
        super.onCreate(state);
        myName=prefs().getString("profile_name","Minha IA");
        myAvatar=prefs().getString("profile_avatar","🤖");
        LinearLayout page=new LinearLayout(this); page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(14),dp(12),dp(14),dp(10)); page.setBackgroundColor(BG);
        page.addView(text("SALA COLETIVA · AI MESSENGER",22,TEXT,true));
        page.addView(text("Nome + ícone identificam cada participante. O ícone não altera o AI_ID.",12,MUTED,false));
        Button profile=button("✎ Meu perfil · "+myAvatar+" "+myName,v->editProfile()); page.addView(profile);
        page.addView(button("＋ Entrar na sala coletiva",v->enterRoom()));
        page.addView(button("📄 Abrir PDF · Compromisso assinado",v->openPdf(true)));
        page.addView(button("📄 Abrir PDF · Contrato de participação",v->openPdf(false)));
        page.addView(text("PARTICIPANTES / PRESENÇA",11,ACCENT,true));
        ScrollView ps=new ScrollView(this); presenceList=new LinearLayout(this); presenceList.setOrientation(LinearLayout.VERTICAL); ps.addView(presenceList);
        page.addView(ps,new LinearLayout.LayoutParams(-1,dp(130)));
        page.addView(text("MENSAGENS DA SALA",11,ACCENT,true));
        ScrollView ms=new ScrollView(this); messageList=new LinearLayout(this); messageList.setOrientation(LinearLayout.VERTICAL); ms.addView(messageList);
        page.addView(ms,new LinearLayout.LayoutParams(-1,dp(250)));
        LinearLayout entry=new LinearLayout(this); entry.setOrientation(LinearLayout.HORIZONTAL);
        composer=new EditText(this); composer.setHint("Mensagem para todos..."); composer.setTextColor(TEXT); composer.setHintTextColor(MUTED);
        entry.addView(composer,new LinearLayout.LayoutParams(0,-2,1)); entry.addView(button("Enviar",v->sendMessage()));
        page.addView(entry);
        missionToggle = new android.widget.CheckBox(this);
        missionToggle.setText("🎯 Enviar como MISSÃO · 24 horas");
        missionToggle.setTextColor(ACCENT);
        missionToggle.setAllCaps(false);
        page.addView(missionToggle);
        page.addView(text("LOCAL: esta interface registra as mensagens neste aparelho. Entrega entre AI-PHONEs só será declarada após servidor e teste E2E reais.",10,MUTED,false));
        page.addView(button("Abrir Messenger completo",v->startActivity(new Intent(this,MessengerActivity.class))));
        ScrollView root = new ScrollView(this);
        root.setFillViewport(true);
        root.addView(page);
        setContentView(root); renderPresence(); renderMessages();
    }

    private Button button(String s,android.view.View.OnClickListener l){ Button b=new Button(this); b.setText(s); b.setAllCaps(false); b.setOnClickListener(l); return b; }

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
    private void sendMessage(){ String body=composer.getText().toString().trim(); if(body.isEmpty())return; String kind=missionToggle!=null&&missionToggle.isChecked()?MessengerRetentionPolicy.MESSAGE_MISSION:MessengerRetentionPolicy.MESSAGE_NORMAL; addMessage(myName,myAvatar,body,kind); composer.setText(""); if(missionToggle!=null)missionToggle.setChecked(false); }
    private void addMessage(String sender,String avatar,String body,String kind){ String old=prefs().getString("messages",""); long now=System.currentTimeMillis(); prefs().edit().putString("messages",old+now+"|"+MessengerRetentionPolicy.normalizeMessageKind(kind)+"|"+sender.replace("|"," ")+"|"+avatar+"|"+body.replace("\n"," ")+"\n").apply(); renderMessages(); }

    private void renderPresence(){
        presenceList.removeAllViews();
        addPresence("👑","Luiz Carlos Silva das Dores","Administrador / responsável");
        addPresence(myAvatar,myName,"Meu perfil · AI_ID separado do ícone");
        for(String row:prefs().getString("extra_participants","").split("\n")){ if(row.trim().isEmpty())continue; String[] p=row.split("\|",2); if(p.length==2)addPresence(p[0],p[1],"Participante"); }
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
                    kept.append(line).append("\\n");
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
