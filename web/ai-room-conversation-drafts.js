(function(root){
 "use strict";
 const MAX_DRAFT_CHARS=5000;
 function createDraftStore(storage,prefix="aiBridgeDraft:"){
  if(!storage||typeof storage.getItem!=="function"||typeof storage.setItem!=="function"||typeof storage.removeItem!=="function")
   throw new Error("DRAFT_STORAGE_REQUIRED");
  function key(conversationId){
   if(typeof conversationId!=="string"||!conversationId.trim())throw new Error("DRAFT_CONVERSATION_REQUIRED");
   return prefix+encodeURIComponent(conversationId.trim());
  }
  return Object.freeze({
   load(conversationId){
    try{const value=storage.getItem(key(conversationId));if(value===null)return "";
     const parsed=JSON.parse(value);return typeof parsed==="string"?parsed.slice(0,MAX_DRAFT_CHARS):"";
    }catch{return "";}
   },
   save(conversationId,draft){
    if(typeof draft!=="string")throw new Error("DRAFT_TEXT_REQUIRED");
    const normalized=draft.slice(0,MAX_DRAFT_CHARS);
    try{if(!normalized.trim()){storage.removeItem(key(conversationId));return true;}
     storage.setItem(key(conversationId),JSON.stringify(normalized));return true;
    }catch{return false;}
   },
   clear(conversationId){
    try{storage.removeItem(key(conversationId));return true;}catch{return false;}
   }
  });
 }
 root.AIBridgeConversationDrafts=Object.freeze({createDraftStore,MAX_DRAFT_CHARS});
})(typeof window!=="undefined"?window:globalThis);
