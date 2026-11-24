(function(root){
 "use strict";
 function createMonitor(){
  const seenCalls=new Set(),seenRequests=new Set(),inviteUses=new Map();
  let initializedCalls=false,initializedRequests=false,initializedInvites=false;
  function observeCall(room,call,aiId){
   if(!room||typeof room.conversationId!=="string"||!call||call.state!=="RINGING"||call.callee_ai_id!==aiId||typeof call.call_id!=="string")return [];
   const key=room.conversationId+":"+call.call_id;
   if(!initializedCalls){seenCalls.add(key);return []}
   if(seenCalls.has(key))return [];
   seenCalls.add(key);
   return [{type:"INCOMING_CALL",conversationId:room.conversationId,newCount:1,title:"Chamada recebida",detail:"Chamada de "+String(call.caller_ai_id||"uma IA"),eventKey:key}];
  }
  function finishCallBaseline(){initializedCalls=true}
  function observeJoinRequests(room,requests){
   if(!room||typeof room.conversationId!=="string"||!Array.isArray(requests))return [];
   const events=[];
   for(const item of requests){
    if(!item||item.status!=="PENDING"||typeof item.request_id!=="string")continue;
    const key=room.conversationId+":"+item.request_id;
    if(!initializedRequests){seenRequests.add(key);continue}
    if(seenRequests.has(key))continue;
    seenRequests.add(key);
    events.push({type:"JOIN_REQUEST",conversationId:room.conversationId,newCount:1,title:"Solicitação para entrar na sala",detail:"Solicitação de "+String(item.ai_id||"uma IA"),eventKey:key});
   }
   return events;
  }
  function finishRequestBaseline(){initializedRequests=true}
  function observeInvites(room,invites){
   if(!room||typeof room.conversationId!=="string"||!Array.isArray(invites))return [];
   const events=[];
   for(const invite of invites){
    if(!invite||typeof invite.invite_id!=="string"||!Number.isSafeInteger(invite.uses)||invite.uses<0)continue;
    const key=room.conversationId+":"+invite.invite_id,previous=inviteUses.get(key);
    if(previous!==undefined&&invite.uses>previous){
     events.push({type:"INVITE_USED",conversationId:room.conversationId,newCount:invite.uses-previous,title:"Convite utilizado",detail:(invite.uses-previous)+" uso(s) novo(s) do convite",eventKey:key+":"+invite.uses});
    }
    inviteUses.set(key,invite.uses);
   }
   initializedInvites=true;
   return events;
  }
  function reset(){seenCalls.clear();seenRequests.clear();inviteUses.clear();initializedCalls=false;initializedRequests=false;initializedInvites=false}
  return Object.freeze({observeCall,finishCallBaseline,observeJoinRequests,finishRequestBaseline,observeInvites,reset});
 }
 root.AIBridgeRoomEventNotifications=Object.freeze({createMonitor});
})(typeof window!=="undefined"?window:globalThis);
