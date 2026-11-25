(function(root){
 "use strict";
 const MAX_TURNS=20;
 function create(options){
  options=options||{};
  if(typeof options.getContext!=="function"||typeof options.onMessage!=="function")
   throw new Error("AI_CONVERSATION_PANEL_DEPENDENCIES_REQUIRED");
  const doc=options.document||root.document;
  if(!doc)throw new Error("AI_CONVERSATION_PANEL_DOCUMENT_REQUIRED");
  const section=doc.getElementById(options.containerId||"conversation");
  if(!section)throw new Error("AI_CONVERSATION_PANEL_CONTAINER_REQUIRED");
  const panel=doc.createElement("section");panel.id="aiConversationPanel";panel.className="request-panel";
  const heading=doc.createElement("strong");heading.textContent="Conversa automática entre duas IAs";
  const description=doc.createElement("p");description.className="sub";description.textContent="Alterna respostas entre as duas identidades da conversa privada. Requer um host com provedores autenticados e verificação de atestado.";
  const prompt=doc.createElement("textarea");prompt.id="aiConversationPrompt";prompt.maxLength=5000;prompt.placeholder="Escreva a mensagem inicial para as duas IAs…";prompt.setAttribute("aria-label","Mensagem inicial da conversa entre IAs");
  const turns=doc.createElement("select");turns.id="aiConversationTurns";turns.setAttribute("aria-label","Quantidade máxima de turnos");
  for(const n of [2,4,6,8,10,12,16,20]){const option=doc.createElement("option");option.value=String(n);option.textContent=n+" turnos";if(n===6)option.selected=true;turns.append(option)}
  const start=doc.createElement("button");start.type="button";start.textContent="Iniciar conversa entre IAs";
  const register=doc.createElement("button");register.type="button";register.textContent="Registrar esta IA na sala";
  const stop=doc.createElement("button");stop.type="button";stop.textContent="Parar";stop.disabled=true;
  const status=doc.createElement("span");status.className="sub";status.setAttribute("role","status");status.setAttribute("aria-live","polite");
  const controls=doc.createElement("div");controls.className="participant-toolbar";controls.append(turns,start,stop,register);
  panel.append(heading,description,prompt,controls,status);
  const composer=doc.getElementById("composer");section.insertBefore(panel,composer||null);
  let runtime=null,running=false,disposed=false;
  function context(){return options.getContext()}
  function allowed(){
   const value=context(),room=value?.room,identity=value?.identity;
   return !!(room&&identity&&room.kind==="PRIVATE"&&Array.isArray(room.memberAiIds)&&room.memberAiIds.length===2&&room.memberAiIds.includes(identity.aiId));
  }
  function host(){
   const value=root.AIBridgeAgentHost;
   return value&&typeof value.requestAgent==="function"&&typeof value.verifyAttestation==="function"?value:null;
  }
  function refresh(){
   const valid=allowed(),provider=host();
   start.disabled=running||!valid||!provider;
   stop.disabled=!running;
   register.disabled=running||!valid||!provider||typeof provider.registerSession!=="function";
   if(running)status.textContent="Conversa em andamento. Turnos concluídos: "+(runtime?.snapshot().turnsCompleted||0)+".";
   else if(!valid)status.textContent="Bloqueado: abra uma conversa privada com exatamente duas identidades autorizadas.";
   else if(!provider)status.textContent="Aguardando host de provedores autenticados. Nenhuma IA foi acionada.";
   else status.textContent="Host disponível. As duas IAs devem registrar suas próprias sessões nesta sala antes do teste.";
  }
  function createRuntime(){
   const provider=host();
   if(!provider)throw new Error("AUTHENTICATED_AGENT_HOST_UNAVAILABLE");
   if(!root.AIBridgeConversationRuntime)throw new Error("AI_CONVERSATION_RUNTIME_UNAVAILABLE");
   return root.AIBridgeConversationRuntime.create({
    getContext:context,
    requestAgent:provider.requestAgent.bind(provider),
    verifyAttestation:provider.verifyAttestation.bind(provider),
    onMessage:async message=>options.onMessage(message),
    onState:snapshot=>{running=snapshot.state==="RUNNING";if(snapshot.state==="RUNNING")status.textContent="Turno "+(snapshot.turnsCompleted+1)+" de "+snapshot.maxTurns+" · aguardando IA autenticada.";else status.textContent=snapshot.state==="STOPPED"?"Conversa interrompida. "+snapshot.turnsCompleted+" turno(s) concluído(s).":"Estado: "+snapshot.state;refresh();}
   });
  }
  async function begin(){
   if(running)return;
   if(!allowed())throw new Error("PRIVATE_TWO_MEMBER_ROOM_REQUIRED");
   if(!host())throw new Error("AUTHENTICATED_AGENT_HOST_UNAVAILABLE");
   const firstMessage=prompt.value.trim(),maxTurns=Number(turns.value);
   if(!firstMessage||firstMessage.length>5000)throw new Error("FIRST_MESSAGE_REQUIRED");
   if(!Number.isSafeInteger(maxTurns)||maxTurns<2||maxTurns>MAX_TURNS)throw new Error("INVALID_TURN_LIMIT");
   runtime=createRuntime();running=true;refresh();
   try{const result=await runtime.start({firstMessage,maxTurns,runId:"rooms-"+Date.now()});status.textContent="Conversa finalizada. "+result.turnsCompleted+" turno(s) concluído(s).";}
   catch(error){status.textContent="Conversa não concluída: "+error.message;}
   finally{running=false;refresh();}
  }
  register.addEventListener("click",async()=>{
   try{
    const provider=host();
    if(!provider||typeof provider.registerSession!=="function")throw new Error("AGENT_SESSION_REGISTRATION_UNAVAILABLE");
    const session=await provider.registerSession();
    refresh();
    status.textContent="Sessão registrada para "+session.aiId+". Validade aproximada: "+Math.round(session.ttlSeconds/60)+" minuto(s).";
   }catch(error){refresh();status.textContent="Não foi possível registrar esta IA: "+error.message;}
  });
  start.addEventListener("click",()=>{begin().catch(error=>{status.textContent="Não foi possível iniciar: "+error.message;refresh()})});
  stop.addEventListener("click",()=>{runtime?.stop();status.textContent="Solicitando parada segura…"});
  function setContext(){if(running&&runtime)runtime.stop();refresh();}
  function dispose(){disposed=true;if(running)runtime?.stop();panel.remove();}
  refresh();
  return Object.freeze({setContext,refresh,dispose,getElement:()=>panel});
 }
 root.AIBridgeConversationPanel=Object.freeze({create});
})(typeof window!=="undefined"?window:globalThis);
