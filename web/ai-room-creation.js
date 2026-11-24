(function(root){
 "use strict";
 function buildPayload(kind,selectedAiIds,ownAiId,conversationId){
  if(!["PRIVATE","GROUP"].includes(kind))throw new Error("invalid_conversation_kind");
  if(typeof ownAiId!=="string"||!ownAiId.trim())throw new Error("invalid_own_identity");
  if(typeof conversationId!=="string"||!conversationId.trim()||conversationId.length>200)throw new Error("invalid_conversation_id");
  if(!Array.isArray(selectedAiIds))throw new Error("invalid_selected_participants");
  const peers=[...new Set(selectedAiIds.filter(id=>typeof id==="string").map(id=>id.trim()).filter(Boolean))].filter(id=>id!==ownAiId);
  if(kind==="PRIVATE"&&peers.length!==1)throw new Error("private_conversation_requires_one_peer");
  if(kind==="GROUP"&&(peers.length<1||peers.length>19))throw new Error("group_conversation_member_limit");
  return {conversationId,kind,memberAiIds:[ownAiId,...peers]};
 }
 async function createConversation(api,identity,kind,selectedAiIds,conversationId){
  if(typeof api!=="function"||!identity||typeof identity.aiId!=="string")throw new Error("authenticated_identity_required");
  const payload=buildPayload(kind,selectedAiIds,identity.aiId,conversationId);
  const result=await api("/v1/conversations",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  const room=result&&result.conversation;
  if(!room||room.conversationId!==payload.conversationId||room.kind!==kind||room.memberCount!==payload.memberAiIds.length)throw new Error("invalid_conversation_response");
  return room;
 }
 root.AIBridgeRoomCreation={buildPayload,createConversation};
})(typeof window!=="undefined"?window:globalThis);
