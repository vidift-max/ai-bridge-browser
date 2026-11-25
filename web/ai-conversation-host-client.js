/* Browser-side client for the server-owned two-agent provider host.
 * Bearer credentials remain in the existing Rooms API closure; this module never reads storage. */
(function(root){
 "use strict";
 function create(options){
  options=options||{};
  if(typeof options.api!=="function"||typeof options.getContext!=="function")
   throw new Error("AI_CONVERSATION_HOST_CLIENT_DEPENDENCIES_REQUIRED");
  function context(){
   const value=options.getContext();
   if(!value||!value.room||!value.identity||value.room.kind!=="PRIVATE"||
      !Array.isArray(value.room.memberAiIds)||value.room.memberAiIds.length!==2||
      !value.room.memberAiIds.includes(value.identity.aiId)||
      typeof value.room.conversationId!=="string"||!value.room.conversationId)
    throw new Error("AI_CONVERSATION_HOST_PRIVATE_ROOM_REQUIRED");
   return {conversationId:value.room.conversationId,aiId:value.identity.aiId};
  }
  async function registerSession(){
   const current=context();
   const result=await options.api("/v1/ai/conversation/session/register",{
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({conversationId:current.conversationId})
   });
   if(!result||!result.session||result.session.conversationId!==current.conversationId||
      result.session.aiId!==current.aiId)
    throw new Error("AI_CONVERSATION_SESSION_REGISTRATION_INVALID");
   return result.session;
  }
  async function requestAgent(request){
   const current=context();
   if(!request||request.conversationId!==current.conversationId||
      !current.aiId||typeof request.agentId!=="string"||
      !currentRoomMembers().includes(request.agentId)||
      typeof request.prompt!=="string"||!request.prompt.trim()||request.prompt.length>5000)
    throw new Error("AI_CONVERSATION_HOST_REQUEST_INVALID");
   const requestId="browser-"+(root.crypto&&typeof root.crypto.randomUUID==="function"?
      root.crypto.randomUUID():Date.now()+"-"+Math.random().toString(16).slice(2));
   const result=await options.api("/v1/ai/conversation/turn",{
    method:"POST",signal:request.signal,headers:{"Content-Type":"application/json"},
    body:JSON.stringify({conversationId:current.conversationId,agentId:request.agentId,
     requestId,prompt:request.prompt.trim()})
   });
   const message=result&&result.message;
   if(!message||message.conversationId!==current.conversationId||
      message.senderAiId!==request.agentId||!Array.isArray(message.recipientAiIds)||
      !message.recipientAiIds.includes(current.aiId)||typeof message.body!=="string"||
      !message.body.trim()||!result.attestation)
    throw new Error("AI_CONVERSATION_HOST_RESPONSE_INVALID");
   return {conversationId:current.conversationId,agentId:request.agentId,
    body:message.body,attestation:JSON.stringify(result.attestation)};
  }
  function currentRoomMembers(){return options.getContext()?.room?.memberAiIds||[];}
  async function verifyAttestation(result){
   const current=context();
   if(!result||typeof result.attestation!=="string"||typeof result.body!=="string")
    return false;
   let attestation;
   try{attestation=JSON.parse(result.attestation)}catch{return false}
   const response=await options.api("/v1/ai/provider/attestation/verify",{
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({conversationId:current.conversationId,
     attestation,responseText:result.body})
   });
   return response?.valid===true;
  }
  return Object.freeze({registerSession,requestAgent,verifyAttestation});
 }
 root.AIBridgeAgentHostClient=Object.freeze({create});
})(typeof window!=="undefined"?window:globalThis);
