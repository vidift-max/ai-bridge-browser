(function(root){
 "use strict";
 function filterRooms(rooms,query,kind){
  if(!Array.isArray(rooms))return [];
  const needle=String(query||"").trim().toLocaleLowerCase();
  return rooms.filter(room=>{
   if(!room||typeof room.conversationId!=="string")return false;
   if(kind&&kind!=="ALL"&&room.kind!==kind)return false;
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
   if(!seen.has(room.conversationId)){seen.add(room.conversationId);merged.push(room)}
  }
  const cursor=page.nextCursor===null||page.nextCursor===undefined?null:page.nextCursor;
  if(cursor!==null&&(typeof cursor!=="string"||!cursor.trim()))throw new Error("invalid_conversation_cursor");
  return {rooms:merged,nextCursor:cursor};
 }
 root.AIBridgeRoomInbox={filterRooms,mergePage};
})(typeof window!=="undefined"?window:globalThis);
