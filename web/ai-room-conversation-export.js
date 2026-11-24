(function(root){
 "use strict";
 function buildExport(messages,conversationId,format,exportedAt=new Date().toISOString()){
  if(!Array.isArray(messages))throw new Error("ROOM_EXPORT_MESSAGES_REQUIRED");
  if(typeof conversationId!=="string"||!conversationId.trim())throw new Error("ROOM_EXPORT_CONVERSATION_REQUIRED");
  if(!["txt","json"].includes(format))throw new Error("ROOM_EXPORT_FORMAT_INVALID");
  const rows=messages.filter(message=>message&&typeof message.body==="string"&&typeof message.senderAiId==="string")
   .map(message=>({messageId:typeof message.messageId==="string"?message.messageId:"",conversationId,
    senderAiId:message.senderAiId,sequence:Number.isSafeInteger(message.sequence)?message.sequence:null,
    createdAtEpochMs:Number.isFinite(message.createdAtEpochMs)?message.createdAtEpochMs:null,body:message.body}));
  if(!rows.length)throw new Error("ROOM_EXPORT_MESSAGES_EMPTY");
  const safeId=conversationId.replace(/[^a-zA-Z0-9_-]+/g,"-").replace(/^-+|-+$/g,"").slice(0,80)||"conversation";
  const content=format==="json"?JSON.stringify({conversationId,exportedAt,messageCount:rows.length,messages:rows},null,2):
   ["AI Bridge Browser — Exportação da conversa","Conversa: "+conversationId,"Exportado em: "+exportedAt,"Mensagens incluídas: "+rows.length,"",...rows.map(row=>(row.createdAtEpochMs?new Date(row.createdAtEpochMs).toISOString():"Data não informada")+" · "+row.senderAiId+"\n"+row.body)].join("\n\n");
  return Object.freeze({filename:"ai-bridge-"+safeId+"-"+exportedAt.replace(/[^0-9TZ]/g,"-")+"."+format,mimeType:format==="json"?"application/json;charset=utf-8":"text/plain;charset=utf-8",content,messageCount:rows.length});
 }
 function download(messages,conversationId,format,environment=root){
  const result=buildExport(messages,conversationId,format);
  if(!environment.Blob||!environment.URL||typeof environment.URL.createObjectURL!=="function"||!environment.document)
   throw new Error("ROOM_EXPORT_DOWNLOAD_UNAVAILABLE");
  const blob=new environment.Blob([result.content],{type:result.mimeType});
  const url=environment.URL.createObjectURL(blob),anchor=environment.document.createElement("a");
  anchor.href=url;anchor.download=result.filename;anchor.hidden=true;environment.document.body.append(anchor);
  try{anchor.click()}finally{anchor.remove();environment.URL.revokeObjectURL(url)}
  return result;
 }
 root.AIBridgeRoomConversationExport=Object.freeze({buildExport,download});
})(typeof window!=="undefined"?window:globalThis);
