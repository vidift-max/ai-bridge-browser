/* Server-authorized room messaging adapter used by the Rooms UI.
 * The server remains authoritative for membership, roles, recipient scope and ACKs. */
(function(root){
 "use strict";
 const MAX_BODY=5000;
 function create(options){
  options=options||{};
  if(typeof options.api!=="function"||typeof options.getContext!=="function"||typeof options.onMessage!=="function")
   throw new Error("ROOM_UI_MESSENGER_DEPENDENCIES_REQUIRED");
  let cursor=0;
  const seen=new Set();
  function context(){
   const value=options.getContext();
   if(!value||!value.room||!value.identity||typeof value.room.conversationId!=="string"||
      !Array.isArray(value.room.memberAiIds)||!value.room.memberAiIds.includes(value.identity.aiId))
    throw new Error("ROOM_UI_MEMBERSHIP_REQUIRED");
   return value;
  }
  async function send(body,ids={}){
   const current=context();
   if(typeof body!=="string"||!body.trim()||body.length>MAX_BODY)throw new Error("INVALID_MESSAGE_BODY");
   const recipients=[...new Set(current.room.memberAiIds.filter(id=>id!==current.identity.aiId))];
   if(!recipients.length)throw new Error("ROOM_UI_RECIPIENTS_REQUIRED");
   const randomId=()=>root.crypto&&root.crypto.randomUUID?root.crypto.randomUUID():String(Date.now())+"-"+Math.random().toString(36).slice(2);
   const payload={messageId:ids.messageId||"msg-"+randomId(),conversationId:current.room.conversationId,
    recipientAiIds:recipients,body:body.trim(),clientRequestId:ids.clientRequestId||"web-"+randomId()};
   const result=await options.api("/v1/messages",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
   options.onMessage({messageId:payload.messageId,senderAiId:current.identity.aiId,body:payload.body,
    sequence:result&&result.sequence,createdAtEpochMs:Date.now()},true);
   return result;
  }
  async function load(){
   const current=context(),roomId=current.room.conversationId;
   const data=await options.api("/v1/conversations/"+encodeURIComponent(roomId)+"/messages?after="+cursor+"&limit=100");
   if(!data||!Array.isArray(data.messages))throw new Error("ROOM_UI_MESSAGE_BATCH_INVALID");
   for(const message of data.messages){
    if(!message||typeof message.messageId!=="string"||!message.messageId||
       message.conversationId!==roomId||typeof message.senderAiId!=="string"||
       typeof message.body!=="string"||!message.body.trim()||message.body.length>MAX_BODY||
       !Number.isSafeInteger(message.sequence)||message.sequence<0)
      throw new Error("ROOM_UI_MESSAGE_INVALID");
    if(seen.has(message.messageId)){
     await options.api("/v1/messages/"+encodeURIComponent(message.messageId)+"/ack",{method:"POST"});
     cursor=Math.max(cursor,message.sequence);
     continue;
    }
    await options.api("/v1/messages/"+encodeURIComponent(message.messageId)+"/ack",{method:"POST"});
    if(options.getContext()?.room?.conversationId!==roomId)return cursor;
    options.onMessage(message,message.senderAiId===current.identity.aiId);
    seen.add(message.messageId);
    cursor=Math.max(cursor,message.sequence);
   }
   return cursor;
  }
  function reset(){cursor=0;seen.clear();}
  return Object.freeze({send,load,reset,getCursor:()=>cursor});
 }
 root.AIBridgeRoomUIMessenger=Object.freeze({create});
})(typeof window!=="undefined"?window:globalThis);
