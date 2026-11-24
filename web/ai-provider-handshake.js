/* Provider-neutral, one-time authentication handshake.
 * Cryptographic proof verification is delegated to a trusted host verifier.
 * This module never stores provider tokens or private keys.
 */
(function(root){
 "use strict";
 var ACTIONS=Object.freeze(["READ_STATUS","SEND_MESSAGE","REQUEST_RECONNECT"]);
 var MAX_PENDING=1024,MAX_TRACKED_NONCES=8192;
 function validId(v){return typeof v==="string"&&/^[A-Za-z0-9._:-]{1,128}$/.test(v);}
 function validCapabilities(value){
  return Array.isArray(value)&&value.length>0&&
   value.every(function(item){return ACTIONS.includes(item);})&&
   new Set(value).size===value.length;
 }
 function create(options){
  options=options||{};
  var verify=typeof options.verifyProof==="function"?options.verifyProof:function(){return false;};
  var now=typeof options.now==="function"?options.now:Date.now;
  var nonceFactory=typeof options.nonceFactory==="function"?options.nonceFactory:function(){
   var bytes=new Uint8Array(24);if(!root.crypto||!root.crypto.getRandomValues)throw new Error("SECURE_RANDOM_UNAVAILABLE");
   root.crypto.getRandomValues(bytes);return Array.from(bytes).map(x=>x.toString(16).padStart(2,"0")).join("");
  };
  var ttl=Math.min(120000,Math.max(5000,Number(options.ttlMs)||30000));
  var maxPending=Number.isInteger(options.maxPendingChallenges)?options.maxPendingChallenges:MAX_PENDING;
  if(maxPending<1||maxPending>MAX_PENDING)throw new Error("MAX_PENDING_INVALID");
  var pending=new Map(),usedNonces=new Map(),stopped=false;
  var audit=typeof options.onAudit==="function"?options.onAudit:function(){};
  function log(event,sessionId,reason){
   try{audit(Object.freeze({event:event,sessionId:sessionId,reason:reason||null,at:now()}));}catch(_){}
  }
  function pruneExpiredNonces(at){
   for(var entry of usedNonces){if(entry[1]<=at)usedNonces.delete(entry[0]);}
  }
  function pruneExpiredChallenges(at){
   for(var entry of pending){
    if(entry[1].expiresAt<=at){pending.delete(entry[0]);log("CHALLENGE_EXPIRED",entry[1].sessionId);}
   }
  }
  function issue(input){
   input=input||{};
   if(stopped)throw new Error("HANDSHAKE_STOPPED");
   if(!validId(input.challengeId)||!validId(input.sessionId)||!validId(input.providerId))throw new Error("INVALID_HANDSHAKE_ID");
   if(!validCapabilities(input.allowedCapabilities))throw new Error("CAPABILITY_GRANT_INVALID");
   var parsed;try{parsed=new URL(input.origin);}catch(_){throw new Error("HTTPS_ORIGIN_REQUIRED");}
   if(parsed.protocol!=="https:"||parsed.username||parsed.password||parsed.pathname!=="/"||parsed.search||parsed.hash||parsed.origin!==input.origin)throw new Error("HTTPS_ORIGIN_REQUIRED");
   var issuedAt=now();
   pruneExpiredChallenges(issuedAt);
   pruneExpiredNonces(issuedAt);
   if(pending.has(input.challengeId))throw new Error("CHALLENGE_ID_REUSED");
   if(pending.size>=maxPending)throw new Error("PENDING_CHALLENGE_LIMIT");
   if(usedNonces.size>=MAX_TRACKED_NONCES)throw new Error("NONCE_TRACKING_LIMIT");
   var nonce=nonceFactory();
   if(typeof nonce!=="string"||nonce.length<32||nonce.length>256||usedNonces.has(nonce))throw new Error("NONCE_INVALID_OR_REUSED");
   usedNonces.set(nonce,issuedAt+ttl);
   var expiresAt=issuedAt+ttl;
   var record={challengeId:input.challengeId,sessionId:input.sessionId,providerId:input.providerId,
    origin:input.origin,nonce:nonce,issuedAt:issuedAt,expiresAt:expiresAt,
    allowedCapabilities:Object.freeze(input.allowedCapabilities.slice())};
   pending.set(record.challengeId,record);
   log("CHALLENGE_ISSUED",record.sessionId);
   return Object.freeze({challengeId:record.challengeId,sessionId:record.sessionId,providerId:record.providerId,
    origin:record.origin,nonce:record.nonce,issuedAt:record.issuedAt,expiresAt:record.expiresAt,
    audience:"ai-bridge-session",allowedCapabilities:record.allowedCapabilities});
  }
  async function verifyResponse(input){
   input=input||{};
   if(stopped)throw new Error("HANDSHAKE_STOPPED");
   var c=pending.get(input.challengeId);
   if(!c)throw new Error("CHALLENGE_NOT_FOUND");
   pending.delete(c.challengeId);
   if(now()>=c.expiresAt){log("HANDSHAKE_REJECTED",c.sessionId,"EXPIRED");throw new Error("CHALLENGE_EXPIRED");}
   if(input.sessionId!==c.sessionId||input.providerId!==c.providerId||input.origin!==c.origin||
      input.nonce!==c.nonce||input.issuedAt!==c.issuedAt||input.expiresAt!==c.expiresAt||
      input.audience!=="ai-bridge-session"){
    log("HANDSHAKE_REJECTED",c.sessionId,"CLAIM_MISMATCH");throw new Error("HANDSHAKE_CLAIM_MISMATCH");
   }
   if(!validCapabilities(input.capabilities)||
      input.capabilities.some(function(capability){return !c.allowedCapabilities.includes(capability);})){
    log("HANDSHAKE_REJECTED",c.sessionId,"CAPABILITY_NOT_GRANTED");throw new Error("CAPABILITY_NOT_GRANTED");
   }
   if(typeof input.proof!=="string"||input.proof.length<16||input.proof.length>8192){
    log("HANDSHAKE_REJECTED",c.sessionId,"PROOF_INVALID");throw new Error("PROOF_INVALID");
   }
   var claims=Object.freeze({challengeId:c.challengeId,sessionId:c.sessionId,providerId:c.providerId,
    origin:c.origin,nonce:c.nonce,issuedAt:c.issuedAt,expiresAt:c.expiresAt,
    audience:"ai-bridge-session",capabilities:Object.freeze(input.capabilities.slice())});
   var valid=false;
   try{valid=await verify(claims,input.proof)===true;}catch(_){valid=false;}
   if(stopped){log("HANDSHAKE_REJECTED",c.sessionId,"STOPPED");throw new Error("HANDSHAKE_STOPPED");}
   if(!valid){log("HANDSHAKE_REJECTED",c.sessionId,"PROOF_UNVERIFIED");throw new Error("PROOF_UNVERIFIED");}
   var result=Object.freeze({status:"AUTHENTICATED",sessionId:c.sessionId,providerId:c.providerId,
    origin:c.origin,capabilities:claims.capabilities,authenticatedAt:now(),expiresAt:c.expiresAt});
   log("HANDSHAKE_VERIFIED",c.sessionId);
   return result;
  }
  function revoke(challengeId){var record=pending.get(challengeId);var ok=pending.delete(challengeId);if(ok)log("CHALLENGE_REVOKED",record.sessionId);return ok;}
  function stop(){stopped=true;pending.clear();usedNonces.clear();log("HANDSHAKE_STOPPED",null);}
  return Object.freeze({issue:issue,verifyResponse:verifyResponse,revoke:revoke,stop:stop,allowedCapabilities:ACTIONS});
 }
 root.AIBridgeProviderHandshake=Object.freeze({create:create,allowedCapabilities:ACTIONS});
})(typeof window!=="undefined"?window:globalThis);
