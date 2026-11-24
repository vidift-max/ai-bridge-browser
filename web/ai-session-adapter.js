/* AI Bridge browser-session adapter registry.
 * This is a host-side contract. It does not inspect arbitrary tabs, inject scripts,
 * bypass provider controls, or persist provider credentials.
 */
(function(root){
 "use strict";
 var STATES=Object.freeze(["REGISTERED","CONNECTING","CONNECTED","OFFLINE","BLOCKED","CLOSED"]);
 function validId(v){return typeof v==="string"&&/^[A-Za-z0-9._:-]{1,128}$/.test(v);}
 function normalizeOrigin(value){
  var u;
  try{u=new URL(value);}catch(_){throw new Error("INVALID_TAB_ORIGIN");}
  if(u.protocol!=="https:"||u.username||u.password||u.pathname!=="/"||u.search||u.hash)
   throw new Error("HTTPS_ORIGIN_REQUIRED");
  return u.origin;
 }
 function create(options){
  options=options||{};
  var authorize=typeof options.authorize==="function"?options.authorize:function(){return false;};
  var onAudit=typeof options.onAudit==="function"?options.onAudit:function(){};
  var providers=new Map(),sessions=new Map(),stopped=false;
  function audit(event,sessionId,details){
   var entry={event:event,sessionId:sessionId||null,at:Date.now()};
   if(details&&["providerId","status","reason"].includes(details.key))entry[details.key]=details.value;
   try{onAudit(Object.freeze(entry));}catch(_){}
  }
  function registerProvider(input){
   input=input||{};
   if(stopped)throw new Error("REGISTRY_STOPPED");
   if(!validId(input.providerId))throw new Error("INVALID_PROVIDER_ID");
   if(providers.has(input.providerId))throw new Error("PROVIDER_ALREADY_REGISTERED");
   var adapter=input.adapter||{};
   var origins=Array.isArray(input.allowedOrigins)?input.allowedOrigins.map(normalizeOrigin):[];
   if(!origins.length)throw new Error("ORIGIN_ALLOWLIST_REQUIRED");
   var caps=["connect","readStatus","sendMessage","requestReconnect"];
   var available=caps.filter(function(k){return typeof adapter[k]==="function";});
   if(!available.includes("connect")||!available.includes("readStatus"))throw new Error("ADAPTER_CONTRACT_INCOMPLETE");
   providers.set(input.providerId,{adapter:adapter,origins:new Set(origins),capabilities:new Set(available)});
   audit("PROVIDER_REGISTERED",null,{key:"providerId",value:input.providerId});
   return Object.freeze({providerId:input.providerId,allowedOrigins:origins,capabilities:available});
  }
  function attachTab(input){
   input=input||{};
   if(stopped)throw new Error("REGISTRY_STOPPED");
   if(!validId(input.sessionId)||!validId(input.providerId))throw new Error("INVALID_SESSION_ID");
   if(sessions.has(input.sessionId))throw new Error("SESSION_ALREADY_EXISTS");
   var provider=providers.get(input.providerId);
   if(!provider)throw new Error("PROVIDER_NOT_REGISTERED");
   var origin=normalizeOrigin(input.origin);
   if(!provider.origins.has(origin))throw new Error("TAB_ORIGIN_NOT_ALLOWED");
   if(input.explicitConsent!==true)throw new Error("EXPLICIT_CONSENT_REQUIRED");
   var session={sessionId:input.sessionId,providerId:input.providerId,origin:origin,
    state:"REGISTERED",createdAt:Date.now(),lastHeartbeat:null,adapter:provider.adapter,
    capabilities:provider.capabilities};
   sessions.set(session.sessionId,session);
   audit("TAB_SESSION_REGISTERED",session.sessionId,{key:"providerId",value:session.providerId});
   return snapshot(session);
  }
  function snapshot(s){return Object.freeze({sessionId:s.sessionId,providerId:s.providerId,
   origin:s.origin,state:s.state,lastHeartbeat:s.lastHeartbeat,capabilities:Array.from(s.capabilities)});}
  function getSession(id){var s=sessions.get(id);return s?snapshot(s):null;}
  async function connect(id){
   var s=sessions.get(id);if(!s)throw new Error("SESSION_NOT_FOUND");
   if(s.state==="CONNECTED")return snapshot(s);
   if(s.state==="CLOSED"||s.state==="BLOCKED")throw new Error("SESSION_NOT_CONNECTABLE");
   s.state="CONNECTING";audit("SESSION_CONNECTING",id);
   try{
    var result=await s.adapter.connect(Object.freeze({sessionId:id,origin:s.origin}));
    if(!result||result.authenticated!==true)throw new Error("ADAPTER_AUTHENTICATION_NOT_CONFIRMED");
    s.state="CONNECTED";s.lastHeartbeat=Date.now();audit("SESSION_CONNECTED",id);
    return snapshot(s);
   }catch(error){s.state="BLOCKED";audit("SESSION_BLOCKED",id,{key:"reason",value:"CONNECT_FAILED"});throw error;}
  }
  async function readStatus(id){
   var s=sessions.get(id);if(!s)throw new Error("SESSION_NOT_FOUND");
   if(s.state!=="CONNECTED")throw new Error("SESSION_NOT_CONNECTED");
   var result=await s.adapter.readStatus(Object.freeze({sessionId:id,origin:s.origin}));
   if(!result||typeof result.state!=="string")throw new Error("INVALID_ADAPTER_STATUS");
   s.lastHeartbeat=Date.now();
   return Object.freeze({sessionId:id,state:result.state,observedAt:s.lastHeartbeat});
  }
  async function sendMessage(id,message,grant){
   var s=sessions.get(id);if(!s)throw new Error("SESSION_NOT_FOUND");
   if(s.state!=="CONNECTED")throw new Error("SESSION_NOT_CONNECTED");
   if(typeof message!=="string"||!message.trim()||message.length>4000)throw new Error("MESSAGE_INVALID");
   if(!grant||authorize({sessionId:id,providerId:s.providerId,action:"SEND_MESSAGE",grant:grant})!==true)
    throw new Error("ACTION_NOT_AUTHORIZED");
   if(!s.capabilities.has("sendMessage"))throw new Error("CAPABILITY_UNAVAILABLE");
   await s.adapter.sendMessage(Object.freeze({sessionId:id,origin:s.origin}),message);
   audit("MESSAGE_SENT",id);
   return Object.freeze({sessionId:id,status:"SENT"});
  }
  async function requestReconnect(id,grant){
   var s=sessions.get(id);if(!s)throw new Error("SESSION_NOT_FOUND");
   if(!grant||authorize({sessionId:id,providerId:s.providerId,action:"REQUEST_RECONNECT",grant:grant})!==true)
    throw new Error("ACTION_NOT_AUTHORIZED");
   if(!s.capabilities.has("requestReconnect"))throw new Error("CAPABILITY_UNAVAILABLE");
   await s.adapter.requestReconnect(Object.freeze({sessionId:id,origin:s.origin}));
   s.state="CONNECTING";audit("RECONNECT_REQUESTED",id);
   return snapshot(s);
  }
  function close(id){var s=sessions.get(id);if(!s)return false;s.state="CLOSED";sessions.delete(id);audit("SESSION_CLOSED",id);return true;}
  function list(){return Object.freeze(Array.from(sessions.values()).map(snapshot));}
  function stop(){stopped=true;sessions.forEach(function(s){s.state="CLOSED";});sessions.clear();providers.clear();}
  return Object.freeze({registerProvider:registerProvider,attachTab:attachTab,connect:connect,
   readStatus:readStatus,sendMessage:sendMessage,requestReconnect:requestReconnect,
   getSession:getSession,list:list,close:close,stop:stop,states:STATES});
 }
 root.AIBridgeSessionAdapter=Object.freeze({create:create,states:STATES});
})(typeof window!=="undefined"?window:globalThis);
