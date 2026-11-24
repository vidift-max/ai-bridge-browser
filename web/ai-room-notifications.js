(function(root){
 "use strict";
 function createTracker(){
  let initialized=false;
  const counts=new Map();
  function observe(rooms,activeConversationId){
   if(!Array.isArray(rooms))throw new Error("invalid_notification_inbox");
   const events=[];
   for(const room of rooms){
    if(!room||typeof room.conversationId!=="string"||!room.conversationId.trim())continue;
    const next=Number.isSafeInteger(room.unreadCount)&&room.unreadCount>0?room.unreadCount:0;
    const previous=counts.get(room.conversationId);
    if(initialized&&room.conversationId!==activeConversationId&&previous!==undefined&&next>previous){
     events.push(Object.freeze({conversationId:room.conversationId,newCount:next-previous,totalUnread:next}));
    }
    counts.set(room.conversationId,next);
   }
   initialized=true;
   return Object.freeze(events);
  }
  function reset(){initialized=false;counts.clear();}
  return Object.freeze({observe,reset});
 }
 function format(events){
  const total=events.reduce((sum,event)=>sum+event.newCount,0);
  if(!total)return "";
  if(events.length===1)return events[0].newCount+" nova mensagem em "+events[0].conversationId;
  return total+" novas mensagens em "+events.length+" conversas";
 }
 root.AIBridgeRoomNotifications=Object.freeze({createTracker,format});
})(typeof window!=="undefined"?window:globalThis);
