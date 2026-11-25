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
  if(!room||room.conversationId!==payload.conversationId||room.kind!==kind||
     room.memberCount!==payload.memberAiIds.length||
     !Array.isArray(room.memberAiIds)||
     payload.memberAiIds.some(id=>!room.memberAiIds.includes(id))||
     room.memberAiIds.length!==payload.memberAiIds.length)
   throw new Error("invalid_conversation_response");
  return room;
 }
 async function createPrivateLink(api,identity,peerAiId,conversationId){
  if(typeof peerAiId!=="string"||!peerAiId.trim()||peerAiId===identity?.aiId)
   throw new Error("private_conversation_requires_one_peer");
  return createConversation(api,identity,"PRIVATE",[peerAiId],conversationId);
 }
 function installLinkButton(documentRef){
  const doc=documentRef||root.document;
  if(!doc||typeof doc.getElementById!=="function")return false;
  const heading=doc.getElementById("conversationCreateHeading");
  const kind=doc.getElementById("conversationKind");
  const peers=doc.getElementById("conversationPeers");
  const create=doc.getElementById("createConversationButton");
  const hint=doc.getElementById("conversationCreateHint");
  if(!heading||!kind||!peers||!create||!hint||doc.getElementById("linkAiButton"))return false;
  const button=doc.createElement("button");
  button.id="linkAiButton";button.type="button";button.textContent="Vincular IA";
  button.setAttribute("aria-describedby","conversationCreateHint");
  button.addEventListener("click",()=>{
   kind.value="PRIVATE";
   kind.dispatchEvent(new Event("change",{bubbles:true}));
   hint.textContent="Vinculação privada: selecione uma identidade já provisionada e autorizada. As abas privadas do ChatGPT não são acessadas nem vinculadas automaticamente.";
   peers.focus();
   peers.scrollIntoView?.({behavior:"smooth",block:"center"});
  });
  heading.insertAdjacentElement("afterend",button);
  const updateLabel=()=>{
   create.textContent=kind.value==="PRIVATE"?"Vincular IA e abrir conversa":"Criar conversa em grupo";
  };
  kind.addEventListener("change",updateLabel);
  updateLabel();
  return true;
 }
 if(root.document){
  if(root.document.readyState==="loading")root.document.addEventListener("DOMContentLoaded",()=>installLinkButton(root.document),{once:true});
  else installLinkButton(root.document);
 }
 root.AIBridgeRoomCreation={buildPayload,createConversation,createPrivateLink,installLinkButton};
})(typeof window!=="undefined"?window:globalThis);
