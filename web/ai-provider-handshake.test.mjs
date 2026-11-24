import {readFile} from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";
const source=await readFile(new URL("./ai-provider-handshake.js",import.meta.url),"utf8");
function fixture(opts={}){
 let time=10000,n=0;const audits=[];
 const context={window:{}};vm.runInNewContext(source,context);
 const h=context.window.AIBridgeProviderHandshake.create({
  now:()=>time,nonceFactory:()=>("nonce-"+String(++n).padStart(32,"0")),
  verifyProof:opts.verifyProof||(()=>true),ttlMs:opts.ttlMs||10000,onAudit:e=>audits.push(e)
 });
 const claims={challengeId:"c1",sessionId:"s1",providerId:"p1",origin:"https://provider.example"};
 const challenge=h.issue(claims);
 function response(extra={}){return {...challenge,capabilities:["READ_STATUS"],proof:"proof-material-long-enough",...extra};}
 return {h,challenge,response,audits,advance(ms){time+=ms;}};
}
test("challenge is scoped to session provider origin and audience",async()=>{
 const f=fixture();const r=await f.h.verifyResponse(f.response());assert.equal(r.status,"AUTHENTICATED");
 assert.equal(r.sessionId,"s1");assert.equal(r.origin,"https://provider.example");
});
test("challenge claims cannot be changed or moved to another session",async()=>{
 const f=fixture();await assert.rejects(f.h.verifyResponse(f.response({sessionId:"s2"})),/HANDSHAKE_CLAIM_MISMATCH/);
});
test("challenge expires after its bounded lifetime",async()=>{
 const f=fixture();f.advance(10001);await assert.rejects(f.h.verifyResponse(f.response()),/CHALLENGE_EXPIRED/);
});
test("challenge is one-time and replay is rejected",async()=>{
 const f=fixture();await f.h.verifyResponse(f.response());
 await assert.rejects(f.h.verifyResponse(f.response()),/CHALLENGE_NOT_FOUND/);
});
test("nonce factory rejects reuse",()=>{
 const context={window:{}};vm.runInNewContext(source,context);const h=context.window.AIBridgeProviderHandshake.create({nonceFactory:()=>"a".repeat(32)});
 h.issue({challengeId:"c1",sessionId:"s1",providerId:"p1",origin:"https://provider.example"});
 assert.throws(()=>h.issue({challengeId:"c2",sessionId:"s2",providerId:"p1",origin:"https://provider.example"}),/NONCE_INVALID_OR_REUSED/);
});
test("proof verifier failure blocks authentication and consumes challenge",async()=>{
 const f=fixture({verifyProof:()=>false});await assert.rejects(f.h.verifyResponse(f.response()),/PROOF_UNVERIFIED/);
 await assert.rejects(f.h.verifyResponse(f.response()),/CHALLENGE_NOT_FOUND/);
});
test("unknown capabilities and duplicate capabilities are rejected",async()=>{
 const f=fixture();await assert.rejects(f.h.verifyResponse(f.response({capabilities:["EXECUTE_JS"]})),/CAPABILITY_INVALID/);
 const g=fixture();await assert.rejects(g.h.verifyResponse(g.response({capabilities:["READ_STATUS","READ_STATUS"]})),/CAPABILITY_INVALID/);
});
test("non-HTTPS origins are rejected before issuing a challenge",()=>{
 const f=fixture();assert.throws(()=>f.h.issue({challengeId:"c2",sessionId:"s2",providerId:"p1",origin:"http://provider.example"}),/HTTPS_ORIGIN_REQUIRED/);
});
test("audit records exclude nonce proof and provider credentials",async()=>{
 const f=fixture();await f.h.verifyResponse(f.response());
 const log=JSON.stringify(f.audits);assert.equal(log.includes(f.challenge.nonce),false);
 assert.equal(log.includes("proof-material-long-enough"),false);
});
test("revocation and shutdown fail closed",async()=>{
 const f=fixture();assert.equal(f.h.revoke("c1"),true);
 await assert.rejects(f.h.verifyResponse(f.response()),/CHALLENGE_NOT_FOUND/);
 f.h.stop();assert.throws(()=>f.h.issue({challengeId:"c2",sessionId:"s2",providerId:"p1",origin:"https://provider.example"}),/HANDSHAKE_STOPPED/);
});
