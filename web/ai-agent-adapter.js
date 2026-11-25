/* Authenticated provider boundary for the bidirectional conversation controller.
 * Provider credentials stay server-side. This browser adapter never claims an identity
 * from request input; it accepts only a server-attested response verified by the host. */
(function(root){
 "use strict";
 const MAX_BODY=5000;
 function create(options){
  options=options||{};
  if(typeof options.getContext!=="function"||typeof options.requestAgent!=="function"||
     typeof options.verifyAttestation!=="function"||typeof options.onMessage!=="function")
   throw new Error("AI_AGENT_ADAPTER_DEPENDENCIES_REQUIRED");
  function context(){
   const value=options.getContext();
   if(!value||!value.room||!value.identity||value.room.kind!=="PRIVATE"||
      !Array.isArray(value.room.memberAiIds)||value.room.memberAiIds.length!==2||
      !value.room.memberAiIds.includes(value.identity.aiId)||
      typeof value.room.conversationId!=="string"||!value.room.conversationId)
    throw new Error("AI_AGENT_PRIVATE_MEMBERSHIP_REQUIRED");
   const peerAiId=value.room.memberAiIds.find(id=>id!==value.identity.aiId);
   if(!peerAiId)throw new Error("AI_AGENT_PEER_REQUIRED");
   return {conversationId:value.room.conversationId,ownAiId:value.identity.aiId,peerAiId};
  }
  async function respond(request){
   const current=context();
   if(!request||request.conversationId!==current.conversationId||
      ![current.ownAiId,current.peerAiId].includes(request.toAiId)||
      request.fromAiId!==current.ownAiId||
      typeof request.prompt!=="string"||!request.prompt.trim()||request.prompt.length>MAX_BODY||
      !Number.isSafeInteger(request.turn)||request.turn<1||
      !Number.isSafeInteger(request.maxTurns)||request.maxTurns<request.turn||
      request.maxTurns>20)
    throw new Error("AI_AGENT_REQUEST_INVALID");
   const result=await options.requestAgent({
    conversationId:current.conversationId,agentId:request.toAiId,
    requesterAiId:current.ownAiId,prompt:request.prompt.trim(),
    turn:request.turn,maxTurns:request.maxTurns,signal:request.signal
   });
   if(options.getContext()?.room?.conversationId!==current.conversationId||
      options.getContext()?.identity?.aiId!==current.ownAiId)
    throw new Error("AI_AGENT_CONTEXT_CHANGED");
   if(!result||result.conversationId!==current.conversationId||
      result.agentId!==request.toAiId||typeof result.body!=="string"||
      !result.body.trim()||result.body.length>MAX_BODY||
      typeof result.attestation!=="string"||!result.attestation||
      !(await options.verifyAttestation(result,{...current,turn:request.turn})))
    throw new Error("AI_AGENT_ATTESTATION_INVALID");
   return {senderAiId:result.agentId,body:result.body.trim(),attestation:result.attestation};
  }
  async function deliver(message){
   const current=context();
   if(!message||message.conversationId!==current.conversationId||
      message.recipientAiId!==current.ownAiId||
      ![current.ownAiId,current.peerAiId].includes(message.senderAiId)||
      typeof message.body!=="string"||!message.body.trim()||message.body.length>MAX_BODY||
      !Number.isSafeInteger(message.turn)||message.turn<1)
    throw new Error("AI_AGENT_DISPLAY_MESSAGE_INVALID");
   await options.onMessage(Object.freeze({...message}));
  }
  return Object.freeze({respond,deliver});
 }
 root.AIBridgeAuthenticatedAgentAdapter=Object.freeze({create});
})(typeof window!=="undefined"?window:globalThis);
