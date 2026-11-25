(function(root){
 "use strict";
 const MIN_TURNS=2,MAX_TURNS=20,DEFAULT_TURNS=6;
 function create(options){
  options=options||{};
  if(typeof options.getContext!=="function"||typeof options.respond!=="function"||typeof options.deliver!=="function")
   throw new Error("CONVERSATION_LOOP_ADAPTERS_REQUIRED");
  let running=false,stopRequested=false,turnsCompleted=0,activeRun=null;
  const listeners=new Set();
  function snapshot(){return Object.freeze({running,stopRequested,turnsCompleted,runId:activeRun?.runId||null,maxTurns:activeRun?.maxTurns||0,state:stopRequested?"STOPPED":running?"RUNNING":"IDLE"});}
  function publish(){const state=snapshot();for(const listener of listeners){try{listener(state);}catch{}}if(typeof options.onState==="function")options.onState(state);}
  function validate(){
   const context=options.getContext();
   if(!context||!context.room||!context.identity||context.room.kind!=="PRIVATE"||
      !Array.isArray(context.room.memberAiIds)||context.room.memberAiIds.length!==2||
      !context.room.memberAiIds.includes(context.identity.aiId))
    throw new Error("PRIVATE_TWO_MEMBER_ROOM_REQUIRED");
   const peerAiId=context.room.memberAiIds.find(id=>id!==context.identity.aiId);
   if(!peerAiId)throw new Error("PRIVATE_PEER_REQUIRED");
   return {conversationId:context.room.conversationId,ownAiId:context.identity.aiId,peerAiId};
  }
  async function start(config){
   if(running)throw new Error("CONVERSATION_LOOP_ALREADY_RUNNING");
   const room=validate(),maxTurns=config?.maxTurns??DEFAULT_TURNS;
   if(!Number.isSafeInteger(maxTurns)||maxTurns<MIN_TURNS||maxTurns>MAX_TURNS)
    throw new Error("INVALID_MAX_TURNS");
   const firstMessage=config?.firstMessage;
   if(typeof firstMessage!=="string"||!firstMessage.trim()||firstMessage.length>5000)
    throw new Error("INVALID_FIRST_MESSAGE");
   running=true;stopRequested=false;turnsCompleted=0;
   const controller=new AbortController();
   activeRun={runId:config?.runId||"run-"+Date.now(),maxTurns,controller,room};
   publish();
   let prompt=firstMessage.trim(),nextSpeaker=room.peerAiId;
   try{
    while(running&&!stopRequested&&turnsCompleted<maxTurns){
     const context=validate();
     if(context.conversationId!==room.conversationId||context.ownAiId!==room.ownAiId||context.peerAiId!==room.peerAiId)
      throw new Error("CONVERSATION_CONTEXT_CHANGED");
     const turn=turnsCompleted+1;
     const response=await options.respond({conversationId:room.conversationId,fromAiId:room.ownAiId,toAiId:nextSpeaker,
      prompt,turn,maxTurns,signal:controller.signal});
     if(stopRequested||controller.signal.aborted)break;
     const afterResponse=validate();
     if(afterResponse.conversationId!==room.conversationId||
        afterResponse.ownAiId!==room.ownAiId||afterResponse.peerAiId!==room.peerAiId)
      throw new Error("CONVERSATION_CONTEXT_CHANGED");
     if(!response||response.senderAiId!==nextSpeaker||typeof response.body!=="string"||
        !response.body.trim()||response.body.length>5000)
      throw new Error("INVALID_AGENT_RESPONSE");
     await options.deliver({conversationId:room.conversationId,senderAiId:response.senderAiId,
      recipientAiId:room.ownAiId,body:response.body.trim(),turn,runId:activeRun.runId});
     turnsCompleted=turn;prompt=response.body.trim();nextSpeaker=nextSpeaker===room.peerAiId?room.ownAiId:room.peerAiId;
     publish();
    }
   }finally{
    running=false;
    if(activeRun){activeRun.controller.abort();activeRun=null;}
    publish();
   }
   return snapshot();
  }
  function stop(){
   if(!running)return snapshot();
   stopRequested=true;
   activeRun?.controller.abort();
   publish();
   return snapshot();
  }
  function subscribe(listener){
   if(typeof listener!=="function")throw new Error("INVALID_STATE_LISTENER");
   listeners.add(listener);listener(snapshot());
   return ()=>listeners.delete(listener);
  }
  return Object.freeze({start,stop,snapshot,subscribe});
 }
 root.AIBridgeConversationLoop=Object.freeze({create,MIN_TURNS,MAX_TURNS,DEFAULT_TURNS});
})(typeof window!=="undefined"?window:globalThis);
