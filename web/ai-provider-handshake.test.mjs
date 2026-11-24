import {readFile} from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";
const source=await readFile(new URL("./ai-provider-handshake.js",import.meta.url),"utf8");
function fixture(opts={}){
 let time=10000,n=0;const audits=[];
 const context={window:{},URL};vm.runInNewContext(source,context);
 const h=context.window.AIBridgeProviderHandshake.create({
  now:()=>time,nonceFactory:()=>"nonce-"+String(++n).padStart(32,"0"),
  verifyProof:opts.verifyProof||(()=>true),ttlMs:opts.ttlMs||10000,
  maxPendingChallenges:opts.maxPendingChallenges,onAudit:e=>audits.push(e)
 });
 const claims={challengeId:"c1",sessionId:"s1",providerId:"p1",
  origin:"https://provider.example",allowedCapabilities:["READ_STATUS"]};
 const challenge=h.issue(claims);
 function response(extra={}){return {...challenge,capabilities:["READ_STATUS"],proof:"proof-material-long-enough",...extra};}
 return {h,challenge,response,audits,advance(ms){time+=ms;}};
}
test("challenge is scoped to session provider origin audience and granted capabilities",async()=>{
 const f=fixture();const r=await f.h.verifyResponse(f.response());assert.equal(r.status,"AUTHENTICATED");
 assert.equal(r.sessionId,"s1");assert.equal(r.origin,"https://provider.example");
 assert.deepEqual(Array.from(r.capabilities),["READ_STATUS"]);
});
test("challenge claims cannot be changed or moved to another session",async()=>{
 const f=fixture();await assert.rejects(f.h.verifyResponse(f.response({sessionId:"s2"})),/HANDSHAKE_CLAIM_MISMATCH/);
});
test("challenge expires at the exact expiry boundary",async()=>{
 const f=fixture();f.advance(10000);await assert.rejects(f.h.verifyResponse(f.response()),/CHALLENGE_EXPIRED/);
});
test("challenge is one-time and replay is rejected",async()=>{
 const f=fixture();await f.h.verifyResponse(f.response());
 await assert.rejects(f.h.verifyResponse(f.response()),/CHALLENGE_NOT_FOUND/);
});
test("nonce factory rejects reuse while nonce is still inside its retention window",()=>{
 const context={window:{},URL};vm.runInNewContext(source,context);const h=context.window.AIBridgeProviderHandshake.create({nonceFactory:()=>"a".repeat(32)});
 const issue=(id)=>h.issue({challengeId:id,sessionId:"s"+id,providerId:"p1",origin:"https://provider.example",allowedCapabilities:["READ_STATUS"]});
 issue("c1");assert.throws(()=>issue("c2"),/NONCE_INVALID_OR_REUSED/);
});
test("proof verifier failure blocks authentication and consumes challenge",async()=>{
 const f=fixture({verifyProof:()=>false});await assert.rejects(f.h.verifyResponse(f.response()),/PROOF_UNVERIFIED/);
 await assert.rejects(f.h.verifyResponse(f.response()),/CHALLENGE_NOT_FOUND/);
});
test("capabilities not granted by the host are rejected",async()=>{
 const f=fixture();await assert.rejects(f.h.verifyResponse(f.response({capabilities:["SEND_MESSAGE"]})),/CAPABILITY_NOT_GRANTED/);
});
test("empty duplicate and unknown capability grants are rejected before challenge creation",()=>{
 const f=fixture();
 const issue=(id,caps)=>f.h.issue({challengeId:id,sessionId:"s2",providerId:"p1",origin:"https://provider.example",allowedCapabilities:caps});
 assert.throws(()=>issue("c2",[]),/CAPABILITY_GRANT_INVALID/);
 assert.throws(()=>issue("c3",["READ_STATUS","READ_STATUS"]),/CAPABILITY_GRANT_INVALID/);
 assert.throws(()=>issue("c4",["EXECUTE_JS"]),/CAPABILITY_GRANT_INVALID/);
});
test("unknown capabilities and duplicate response capabilities are rejected",async()=>{
 const f=fixture();await assert.rejects(f.h.verifyResponse(f.response({capabilities:["EXECUTE_JS"]})),/CAPABILITY_NOT_GRANTED/);
 const g=fixture();await assert.rejects(g.h.verifyResponse(g.response({capabilities:["READ_STATUS","READ_STATUS"]})),/CAPABILITY_NOT_GRANTED/);
});
test("non-HTTPS origins are rejected before issuing a challenge",()=>{
 const f=fixture();assert.throws(()=>f.h.issue({challengeId:"c2",sessionId:"s2",providerId:"p1",origin:"http://provider.example",allowedCapabilities:["READ_STATUS"]}),/HTTPS_ORIGIN_REQUIRED/);
});
test("pending challenge capacity is bounded and expired entries are pruned",()=>{
 const context={window:{},URL};vm.runInNewContext(source,context);let time=1,n=0;
 const h=context.window.AIBridgeProviderHandshake.create({now:()=>time,ttlMs:5000,maxPendingChallenges:1,
  nonceFactory:()=>"nonce-"+String(++n).padStart(32,"0")});
 const issue=(id)=>h.issue({challengeId:id,sessionId:"s"+id,providerId:"p1",origin:"https://provider.example",allowedCapabilities:["READ_STATUS"]});
 issue("c1");assert.throws(()=>issue("c2"),/PENDING_CHALLENGE_LIMIT/);
 time=5001;assert.equal(issue("c2").challengeId,"c2");
});
test("nonce tracking capacity fails closed",()=>{
 const context={window:{},URL};vm.runInNewContext(source,context);let n=0;
 const h=context.window.AIBridgeProviderHandshake.create({nonceFactory:()=>"nonce-"+String(++n).padStart(32,"0")});
 for(let i=0;i<8192;i++)h.issue({challengeId:"c"+i,sessionId:"s"+i,providerId:"p1",origin:"https://provider.example",allowedCapabilities:["READ_STATUS"]});
 assert.throws(()=>h.issue({challengeId:"overflow",sessionId:"overflow",providerId:"p1",origin:"https://provider.example",allowedCapabilities:["READ_STATUS"]}),/NONCE_TRACKING_LIMIT/);
});
test("audit records exclude nonce proof and provider credentials",async()=>{
 const f=fixture();await f.h.verifyResponse(f.response());
 const log=JSON.stringify(f.audits);assert.equal(log.includes(f.challenge.nonce),false);
 assert.equal(log.includes("proof-material-long-enough"),false);
});
test("revocation and shutdown fail closed",async()=>{
 const f=fixture();assert.equal(f.h.revoke("c1"),true);
 await assert.rejects(f.h.verifyResponse(f.response()),/CHALLENGE_NOT_FOUND/);
 f.h.stop();assert.throws(()=>f.h.issue({challengeId:"c2",sessionId:"s2",providerId:"p1",origin:"https://provider.example",allowedCapabilities:["READ_STATUS"]}),/HANDSHAKE_STOPPED/);
});
test("shutdown during asynchronous proof verification prevents authentication",async()=>{
 let release;const gate=new Promise(resolve=>{release=resolve;});
 const f=fixture({verifyProof:()=>gate.then(()=>true)});
 const verification=f.h.verifyResponse(f.response());f.h.stop();release();
 await assert.rejects(verification,/HANDSHAKE_STOPPED/);
});
