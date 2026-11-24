(function(root){
 "use strict";
 const MAX_QUOTE_CHARS=4000;
 function buildReplyDraft(message){
  if(!message||typeof message!=="object"||typeof message.body!=="string"||!message.body.trim())throw new Error("ROOM_REPLY_MESSAGE_REQUIRED");
  const sender=typeof message.senderAiId==="string"&&message.senderAiId.trim()?message.senderAiId.trim():"IA";
  const original=message.body.length>MAX_QUOTE_CHARS?message.body.slice(0,MAX_QUOTE_CHARS)+"…":message.body;
  const quote=original.split(/\\r?\\n/).map(line=>"> "+line).join("\\n");
  return "↪ Resposta a "+sender+":\\n"+quote+"\\n\\n";
 }
 root.AIBridgeRoomMessageReply=Object.freeze({buildReplyDraft});
})(typeof window!=="undefined"?window:globalThis);
