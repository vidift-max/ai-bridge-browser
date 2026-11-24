/* Room-scoped messaging bridge; delegates membership decisions to the host admission service. */
(function(root){
 "use strict";
 const MAX_BODY=5000;
 function validId(value){return typeof value==="string"&&/^[A-Za-z0-9._:-]{1,128}$/.test(value);}
 function create(options){
  options=options||{};
  const admission=options.admission;
  const sendTransport=options.sendTransport;
  const acknowledge=options.acknowledge;
  const deliver=options.deliver;
  if(!admission||typeof admission.getRoom!=="function"||typeof admission.authorizeMessage!=="function"||typeof admission.authorizeRead!=="function")
   throw new Error("ROOM_ADMISSION_REQUIRED");
  if(typeof sendTransport!=="function"||typeof acknowledge!=="function"||typeof deliver!=="function")
   throw new Error("MESSAGING_CALLBACKS_REQUIRED");
  const seen=new Set(),processing=new Set();
  function activeMember(roomId,aiId){
   const room=admission.getRoom(roomId);
   if(!room||room.status!=="ACTIVE")throw new Error("ROOM_NOT_ACTIVE");
   const member=room.participants.find(p=>p.aiId===aiId&&p.status==="ACTIVE");
   if(!member)throw new Error("ROOM_MEMBERSHIP_REQUIRED");
   admission.authorizeRead({roomId,aiId,sessionId:member.sessionId});
   return {room,member};
  }
  function createPayload(input){
   input=input||{};
   if(!validId(input.roomId)||!validId(input.aiId)||!validId(input.sessionId))
    throw new Error("MESSAGE_IDENTITY_INVALID");
   if(typeof input.body!=="string"||!input.body.trim()||input.body.length>MAX_BODY)
    throw new Error("INVALID_MESSAGE_BODY");
   const authorized=admission.authorizeMessage({roomId:input.roomId,aiId:input.aiId,sessionId:input.sessionId});
   const room=admission.getRoom(input.roomId);
   if(!room||room.status!=="ACTIVE")throw new Error("ROOM_NOT_ACTIVE");
   const recipients=room.participants.filter(p=>p.status==="ACTIVE"&&p.aiId!==input.aiId&&p.role!=="OBSERVER").map(p=>p.aiId);
   if(!recipients.length)throw new Error("ROOM_RECIPIENTS_UNAVAILABLE");
   return Object.freeze({
    messageId:input.messageId||globalThis.crypto.randomUUID(),
    roomId:input.roomId,senderAiId:authorized.aiId,senderSessionId:authorized.sessionId,
    recipientAiIds:Object.freeze(recipients),body:input.body.trim(),
    clientRequestId:input.clientRequestId||globalThis.crypto.randomUUID(),
    sequence:input.sequence===undefined?null:input.sequence,messageKind:"ROOM"
   });
  }
  async function send(input){
   const payload=createPayload(input);
   const result=await sendTransport(payload);
   admission.authorizeMessage({roomId:payload.roomId,aiId:payload.senderAiId,sessionId:payload.senderSessionId});
   return Object.freeze({messageId:payload.messageId,roomId:payload.roomId,senderAiId:payload.senderAiId,
    recipientAiIds:payload.recipientAiIds,sequence:result&&result.sequence});
  }
  async function receive(input){
   input=input||{};
   const message=input.message,localAiId=input.localAiId,localSessionId=input.localSessionId;
   if(!message||!validId(message.messageId)||!validId(message.roomId)||!validId(message.senderAiId)||
      !validId(localAiId)||!validId(localSessionId)||!Array.isArray(message.recipientAiIds)||
      !message.recipientAiIds.includes(localAiId)||new Set(message.recipientAiIds).size!==message.recipientAiIds.length||message.recipientAiIds.some(id=>!validId(id))||typeof message.body!=="string"||
      !message.body.trim()||message.body.length>MAX_BODY||!Number.isSafeInteger(message.sequence)||message.sequence<0)
    throw new Error("INBOUND_MESSAGE_INVALID");
   const dedupeKey=message.roomId+":"+message.messageId;
   if(seen.has(dedupeKey)){
    await acknowledge({messageId:message.messageId,roomId:message.roomId,sequence:message.sequence});
    return Object.freeze({status:"DUPLICATE_ACKNOWLEDGED",messageId:message.messageId});
   }
   if(processing.has(dedupeKey))throw new Error("MESSAGE_ALREADY_PROCESSING");
   processing.add(dedupeKey);
   try{
    const {member}=activeMember(message.roomId,message.senderAiId);
    if(member.role==="OBSERVER")throw new Error("SENDER_ROLE_READ_ONLY");
    const local=admission.getRoom(message.roomId).participants.find(p=>p.aiId===localAiId&&p.status==="ACTIVE");
    if(!local||local.sessionId!==localSessionId)throw new Error("LOCAL_ROOM_MEMBERSHIP_REQUIRED");
    admission.authorizeRead({roomId:message.roomId,aiId:localAiId,sessionId:localSessionId});
    await deliver(Object.freeze({messageId:message.messageId,roomId:message.roomId,
     senderAiId:message.senderAiId,recipientAiIds:Object.freeze([...message.recipientAiIds]),
     body:message.body,sequence:message.sequence}));
    admission.authorizeMessage({roomId:message.roomId,aiId:message.senderAiId,sessionId:member.sessionId});
    admission.authorizeRead({roomId:message.roomId,aiId:localAiId,sessionId:localSessionId});
    await acknowledge({messageId:message.messageId,roomId:message.roomId,sequence:message.sequence});
    seen.add(dedupeKey);
    return Object.freeze({status:"DELIVERED_AND_ACKNOWLEDGED",messageId:message.messageId});
   } finally {processing.delete(dedupeKey);}
  }
  function clear(){seen.clear();processing.clear();}
  return Object.freeze({createPayload,send,receive,clear});
 }
 root.AIBridgeRoomMessenger=Object.freeze({create:create});
})(typeof window!=="undefined"?window:globalThis);
