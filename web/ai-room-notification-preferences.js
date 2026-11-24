(function(root){
 "use strict";
 const DEFAULTS=Object.freeze({enabled:true,privateEnabled:true,groupEnabled:true,browserEnabled:true});
 function normalize(value){
  if(!value||typeof value!=="object"||Array.isArray(value))return {...DEFAULTS};
  return {enabled:value.enabled!==false,privateEnabled:value.privateEnabled!==false,groupEnabled:value.groupEnabled!==false,browserEnabled:value.browserEnabled!==false};
 }
 function createPreferences(storage,key){
  if(!storage||typeof storage.getItem!=="function"||typeof storage.setItem!=="function")throw new Error("invalid_notification_preferences_storage");
  if(typeof key!=="string"||!key.trim())throw new Error("invalid_notification_preferences_key");
  function get(){try{return normalize(JSON.parse(storage.getItem(key)||"null"))}catch{return {...DEFAULTS}}}
  function update(patch){
   if(!patch||typeof patch!=="object"||Array.isArray(patch))throw new Error("invalid_notification_preferences_patch");
   const current=get(),next={...current};
   for(const field of Object.keys(DEFAULTS))if(Object.prototype.hasOwnProperty.call(patch,field))next[field]=patch[field]===true;
   storage.setItem(key,JSON.stringify(next));return Object.freeze({...next});
  }
  function allows(kind){
   const value=get();
   if(!value.enabled)return false;
   if(kind==="PRIVATE")return value.privateEnabled;
   if(kind==="GROUP")return value.groupEnabled;
   return false;
  }
  function reset(){storage.removeItem?.(key);return get()}
  return Object.freeze({get,update,allows,reset});
 }
 root.AIBridgeNotificationPreferences=Object.freeze({createPreferences,defaults:DEFAULTS});
})(typeof window!=="undefined"?window:globalThis);
