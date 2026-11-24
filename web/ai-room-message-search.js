(function(root){
 "use strict";
 function filterMessages(messages,query,sender){
  if(!Array.isArray(messages))throw new Error("ROOM_MESSAGES_REQUIRED");
  const term=typeof query==="string"?query.trim().toLocaleLowerCase():String(query||"").toLocaleLowerCase();
  const author=typeof sender==="string"?sender.trim().toLocaleLowerCase():"";
  return messages.filter(message=>{
   if(!message||typeof message.body!=="string")return false;
   const by=typeof message.senderAiId==="string"?message.senderAiId.toLocaleLowerCase():"";
   return (!author||by===author)&&(!term||message.body.toLocaleLowerCase().includes(term)||by.includes(term));
  });
 }
 root.AIBridgeRoomMessageSearch=Object.freeze({filterMessages});
})(typeof window!=="undefined"?window:globalThis);
