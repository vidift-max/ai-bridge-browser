(function(root){
 "use strict";
 function filterRooms(rooms,query,kind,view="ALL",pinnedIds=[]){
  if(!Array.isArray(rooms))return [];
  const needle=String(query||"").trim().toLocaleLowerCase();
  return rooms.filter(room=>{
   if(!room||typeof room.conversationId!=="string")return false;
   if(kind&&kind!=="ALL"&&room.kind!==kind)return false;
   if(view==="UNREAD"&&!(Number.isSafeInteger(room.unreadCount)&&room.unreadCount>0))return false;
   if(view==="PINNED"&&(!Array.isArray(pinnedIds)||!pinnedIds.includes(room.conversationId)))return false;
   if(view!=="ALL"&&view!=="UNREAD"&&view!=="PINNED")return false;
   if(!needle)return true;
   const preview=room.lastMessage&&typeof room.lastMessage.body==="string"?room.lastMessage.body:"";
   const haystack=[room.conversationId,room.kind,preview,...(Array.isArray(room.memberAiIds)?room.memberAiIds:[])].join(" ").toLocaleLowerCase();
   return haystack.includes(needle);
  });
 }
 function mergePage(existing,page){
  if(!Array.isArray(existing)||!Array.isArray(page?.conversations))throw new Error("invalid_conversation_page");
  const seen=new Set(existing.map(room=>room.conversationId));
  const merged=[...existing];
  for(const room of page.conversations){
   if(!room||typeof room.conversationId!=="string"||!room.conversationId)throw new Error("invalid_conversation_record");
   if(room.unreadCount!==undefined&&(!Number.isSafeInteger(room.unreadCount)||room.unreadCount<0))
    throw new Error("invalid_conversation_unread_count");
   if(room.lastMessage!==undefined&&room.lastMessage!==null){
    const last=room.lastMessage;
    if(!last||typeof last.messageId!=="string"||!last.messageId||
       typeof last.senderAiId!=="string"||typeof last.body!=="string"||
       last.body.length>5000||!Number.isSafeInteger(last.sequence)||last.sequence<0)
     throw new Error("invalid_conversation_last_message");
   }
   if(!seen.has(room.conversationId)){seen.add(room.conversationId);merged.push(room)}
  }
  const cursor=page.nextCursor===null||page.nextCursor===undefined?null:page.nextCursor;
  if(cursor!==null&&(typeof cursor!=="string"||!cursor.trim()))throw new Error("invalid_conversation_cursor");
  return {rooms:merged,nextCursor:cursor};
 }
 root.AIBridgeRoomInbox={filterRooms,mergePage};
})(typeof window!=="undefined"?window:globalThis);
