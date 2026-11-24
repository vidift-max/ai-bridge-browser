/* AI Bridge browser-session adapter registry.
 * Host-side contract only: no tab scraping, credential persistence or login bypass.
 * A tab must present a verified, unexpired provider handshake bound to its session.
 */
(function(root){
 "use strict";
 var STATES=Object.freeze(["REGISTERED","CONNECTING","CONNECTED","OFFLINE","BLOCKED","CLOSED"]);
 var ACTIONS=Object.freeze(["READ_STATUS","SEND_MESSAGE","REQUEST_RECONNECT"]);
 function validId(v){return typeof v==="string"&&/^[A-Za-z0-9._:-]{1,128}$/.test(v);}
 function normalizeOrigin(value){
  var u;try{u=new URL(value);}catch(_){throw new Error("INVALID_TAB_ORIGIN");}
  if(u.protocol!=="https:"||u.username||u.password||u.pathname!=="/"||u.search||u.hash)throw new Error("HTTPS_ORIGIN_REQUIRED");
  return u.origin;
 }
 function create(options){
  options=options||{};
  var authorize=typeof options.authorize==="function"?options.authorize:function(){return false;};
  var onAudit=typeof options.onAudit==="function"?options.onAudit:function(){};
  var now=typeof options.now==="function"?options.now:Date.now;
  var providers=new Map(),sessions=new Map(),stopped=false;
  function audit(event,sessionId,details){
   var entry={event:event,sessionId:sessionId||null,at:now()};
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
  function validateHandshake(handshake,input,origin){
   if(!handshake||handshake.status!=="AUTHENTICATED")throw new Error("VERIFIED_HANDSHAKE_REQUIRED");
   if(handshake.sessionId!==input.sessionId||handshake.providerId!==input.providerId||handshake.origin!==origin)
    throw new Error("HANDSHAKE_SESSION_BINDING_MISMATCH");
   if(!Number.isFinite(handshake.expiresAt)||now()>=handshake.expiresAt)
    throw new Error("HANDSHAKE_EXPIRED");
   if(!Array.isArray(handshake.capabilities)||!handshake.capabilities.length||
      handshake.capabilities.some(function(cap){return !ACTIONS.includes(cap);})||
      new Set(handshake.capabilities).size!==handshake.capabilities.length)
    throw new Error("HANDSHAKE_CAPABILITIES_INVALID");
   return new Set(handshake.capabilities);
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
   var grants=validateHandshake(input.handshake,input,origin);
   var session={sessionId:input.sessionId,providerId:input.providerId,origin:origin,
    state:"REGISTERED",createdAt:now(),lastHeartbeat:null,adapter:provider.adapter,
    adapterCapabilities:provider.capabilities,grantedCapabilities:grants};
   sessions.set(session.sessionId,session);
   audit("TAB_SESSION_REGISTERED",session.sessionId,{key:"providerId",value:session.providerId});
   return snapshot(session);
  }
  function snapshot(s){return Object.freeze({sessionId:s.sessionId,providerId:s.providerId,
   origin:s.origin,state:s.state,lastHeartbeat:s.lastHeartbeat,
   capabilities:ACTIONS.filter(function(cap){return s.grantedCapabilities.has(cap);})});}
  function getSession(id){var s=sessions.get(id);return s?snapshot(s):null;}
  function requireCapability(s,cap){
   if(!s.grantedCapabilities.has(cap))throw new Error("CAPABILITY_NOT_GRANTED");
  }
  async function connect(id){
   var s=sessions.get(id);if(!s)throw new Error("SESSION_NOT_FOUND");
   if(s.state==="CONNECTED")return snapshot(s);
   if(s.state==="CLOSED"||s.state==="BLOCKED")throw new Error("SESSION_NOT_CONNECTABLE");
   s.state="CONNECTING";audit("SESSION_CONNECTING",id);
   try{
    var result=await s.adapter.connect(Object.freeze({sessionId:id,origin:s.origin}));
    if(sessions.get(id)!==s||s.state!=="CONNECTING")throw new Error("SESSION_NO_LONGER_ACTIVE");
    if(!result||result.authenticated!==true)throw new Error("ADAPTER_AUTHENTICATION_NOT_CONFIRMED");
    s.state="CONNECTED";s.lastHeartbeat=now();audit("SESSION_CONNECTED",id);
    return snapshot(s);
   }catch(error){
    if(sessions.get(id)===s&&s.state==="CONNECTING"){s.state="BLOCKED";audit("SESSION_BLOCKED",id,{key:"reason",value:"CONNECT_FAILED"});}
    throw error;
   }
  }
  async function readStatus(id){
   var s=sessions.get(id);if(!s)throw new Error("SESSION_NOT_FOUND");
   if(s.state!=="CONNECTED")throw new Error("SESSION_NOT_CONNECTED");
   requireCapability(s,"READ_STATUS");
   var result=await s.adapter.readStatus(Object.freeze({sessionId:id,origin:s.origin}));
   if(sessions.get(id)!==s||s.state!=="CONNECTED")throw new Error("SESSION_NO_LONGER_ACTIVE");
   if(!result||typeof result.state!=="string")throw new Error("INVALID_ADAPTER_STATUS");
   s.lastHeartbeat=now();
   return Object.freeze({sessionId:id,state:result.state,observedAt:s.lastHeartbeat});
  }
  async function sendMessage(id,message,grant){
   var s=sessions.get(id);if(!s)throw new Error("SESSION_NOT_FOUND");
   if(s.state!=="CONNECTED")throw new Error("SESSION_NOT_CONNECTED");
   requireCapability(s,"SEND_MESSAGE");
   if(typeof message!=="string"||!message.trim()||message.length>4000)throw new Error("MESSAGE_INVALID");
   if(!grant||authorize({sessionId:id,providerId:s.providerId,action:"SEND_MESSAGE",grant:grant})!==true)
    throw new Error("ACTION_NOT_AUTHORIZED");
   if(!s.adapterCapabilities.has("sendMessage"))throw new Error("CAPABILITY_UNAVAILABLE");
   await s.adapter.sendMessage(Object.freeze({sessionId:id,origin:s.origin}),message);
   if(sessions.get(id)!==s||s.state!=="CONNECTED")throw new Error("SESSION_NO_LONGER_ACTIVE");
   audit("MESSAGE_SENT",id);
   return Object.freeze({sessionId:id,status:"SENT"});
  }
  async function requestReconnect(id,grant){
   var s=sessions.get(id);if(!s)throw new Error("SESSION_NOT_FOUND");
   if(s.state!=="CONNECTED")throw new Error("SESSION_NOT_CONNECTED");
   requireCapability(s,"REQUEST_RECONNECT");
   if(!grant||authorize({sessionId:id,providerId:s.providerId,action:"REQUEST_RECONNECT",grant:grant})!==true)
    throw new Error("ACTION_NOT_AUTHORIZED");
   if(!s.adapterCapabilities.has("requestReconnect"))throw new Error("CAPABILITY_UNAVAILABLE");
   await s.adapter.requestReconnect(Object.freeze({sessionId:id,origin:s.origin}));
   if(sessions.get(id)!==s||s.state!=="CONNECTED")throw new Error("SESSION_NO_LONGER_ACTIVE");
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
 root.AIBridgeSessionAdapter=Object.freeze({create:create,states:STATES,allowedCapabilities:ACTIONS});
})(typeof window!=="undefined"?window:globalThis);
