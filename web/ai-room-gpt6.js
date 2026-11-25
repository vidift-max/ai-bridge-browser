/* GPT-6 opt-in bridge for the primary Rooms composer. */
(function(root){
 "use strict";
 const ASSISTANT_ID="AI-GPT6",MAX_BODY=5000;
 function create(options){
  options=options||{};
  if(typeof options.api!=="function"||typeof options.getContext!=="function")
   throw new Error("ROOM_GPT6_DEPENDENCIES_REQUIRED");
  async function respond(body,clientRequestId){
   const current=options.getContext();
   if(!current||!current.room||!current.identity||
      typeof current.room.conversationId!=="string"||
      !Array.isArray(current.room.memberAiIds)||
      !current.room.memberAiIds.includes(current.identity.aiId))
    throw new Error("ROOM_GPT6_MEMBERSHIP_REQUIRED");
   if(!current.room.memberAiIds.includes(ASSISTANT_ID))
    throw new Error("ROOM_GPT6_NOT_SELECTED");
   if(current.identity.aiId===ASSISTANT_ID)
    throw new Error("ROOM_GPT6_USER_IDENTITY_REQUIRED");
   if(typeof body!=="string"||!body.trim()||body.length>MAX_BODY)
    throw new Error("ROOM_GPT6_INVALID_MESSAGE");
   if(typeof clientRequestId!=="string"||clientRequestId.length<8||
      clientRequestId.length>128||!/^[A-Za-z0-9._:-]+$/.test(clientRequestId))
    throw new Error("ROOM_GPT6_INVALID_REQUEST_ID");
   const result=await options.api("/v1/gpt6/room/respond",{
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({conversationId:current.room.conversationId,
     message:body.trim(),clientRequestId})
   });
   const user=result&&result.userMessage,assistant=result&&result.assistantMessage;
   if(!user||user.conversationId!==current.room.conversationId||
      user.senderAiId!==current.identity.aiId||
      !assistant||assistant.conversationId!==current.room.conversationId||
      assistant.senderAiId!==ASSISTANT_ID||typeof assistant.body!=="string"||
      !assistant.body.trim()||!Number.isSafeInteger(assistant.sequence))
    throw new Error("ROOM_GPT6_RESPONSE_INVALID");
   return result;
  }
  return Object.freeze({respond});
 }
 root.AIBridgeRoomGPT6=Object.freeze({create});
})(typeof window!=="undefined"?window:globalThis);
