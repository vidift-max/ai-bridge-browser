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

 function createCenter(storage,key="aiBridgeNotificationCenter",limit=100){
  if(!storage||typeof storage.getItem!=="function"||typeof storage.setItem!=="function")throw new Error("invalid_notification_storage");
  if(!Number.isSafeInteger(limit)||limit<1||limit>500)throw new Error("invalid_notification_limit");
  let serial=0;
  function read(){
   let parsed;
   try{parsed=JSON.parse(storage.getItem(key)||"[]")}catch{parsed=[]}
   if(!Array.isArray(parsed))return [];
   return parsed.filter(item=>item&&typeof item.id==="string"&&typeof item.conversationId==="string"&&item.conversationId.trim().length>0&&Number.isSafeInteger(item.newCount)&&item.newCount>0&&typeof item.createdAt==="string"&&typeof item.read==="boolean").slice(0,limit);
  }
  function write(items){storage.setItem(key,JSON.stringify(items.slice(0,limit)));return items.slice(0,limit)}
  function list(){return Object.freeze(read().map(item=>Object.freeze({...item})));}
  function record(events,createdAt=new Date().toISOString()){
   if(!Array.isArray(events))throw new Error("invalid_notification_events");
   const items=read();
   for(const event of events){
    if(!event||typeof event.conversationId!=="string"||!event.conversationId.trim()||!Number.isSafeInteger(event.newCount)||event.newCount<1)continue;
    serial+=1;
    items.unshift({id:"notice-"+Date.now()+"-"+serial,conversationId:event.conversationId,newCount:event.newCount,createdAt,read:false});
   }
   return Object.freeze(write(items).map(item=>Object.freeze({...item})));
  }
  function markRead(id){if(typeof id!=="string")return list();return Object.freeze(write(read().map(item=>item.id===id?{...item,read:true}:item)).map(item=>Object.freeze({...item})));}
  function markAllRead(){return Object.freeze(write(read().map(item=>({...item,read:true}))).map(item=>Object.freeze({...item})));}
  function unreadCount(){return read().filter(item=>!item.read).length;}
  return Object.freeze({list,record,markRead,markAllRead,unreadCount});
 }
 root.AIBridgeRoomNotifications=Object.freeze({createTracker,format,createCenter});
})(typeof window!=="undefined"?window:globalThis);
