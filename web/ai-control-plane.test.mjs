import { readFile } from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";
const source=await readFile(new URL("./ai-control-plane.js",import.meta.url),"utf8");
function fixture(){
 let clock=100000; const calls=[],audits=[];
 const adapter={
  async sendMessage(id,msg){calls.push(["send",id,msg]);return {secret:"private"};},
  async requestReconnect(id){calls.push(["reconnect",id]);},
  async readStatus(id){calls.push(["status",id]);return {state:"READY",token:"secret"};}
 };
 const context={window:{}}; vm.runInNewContext(source,context);
 const plane=context.window.AIBridgeControlPlane.create({adapter,now:()=>clock,onAudit:e=>audits.push(e),
  baseDelayMs:1000,maxDelayMs:4000,maxRecoveryAttempts:2});
 return {plane,calls,audits,advance(ms){clock+=ms;},now(){return clock;}};
}
test("only explicitly granted allowlisted actions execute",async()=>{
 const f=fixture(); f.plane.issueGrant({grantId:"g1",sessionId:"s1",actions:["SEND_MESSAGE"],ttlMs:5000});
 await assert.rejects(f.plane.execute({actionId:"a0",grantId:"g1",sessionId:"s1",action:"READ_STATUS"}),/ACTION_NOT_AUTHORIZED/);
 await f.plane.execute({actionId:"a1",grantId:"g1",sessionId:"s1",action:"SEND_MESSAGE",message:"hello"});
 assert.deepEqual(f.calls,[["send","s1","hello"]]);
});
test("grant is session-bound, expires, and enforces use count",async()=>{
 const f=fixture(); f.plane.issueGrant({grantId:"g1",sessionId:"s1",actions:["READ_STATUS"],ttlMs:1000,maxUses:1});
 await assert.rejects(f.plane.execute({actionId:"wrong",grantId:"g1",sessionId:"s2",action:"READ_STATUS"}),/ACTION_NOT_AUTHORIZED/);
 await f.plane.execute({actionId:"a1",grantId:"g1",sessionId:"s1",action:"READ_STATUS"});
 await assert.rejects(f.plane.execute({actionId:"a2",grantId:"g1",sessionId:"s1",action:"READ_STATUS"}),/ACTION_NOT_AUTHORIZED/);
 f.plane.issueGrant({grantId:"g2",sessionId:"s1",actions:["READ_STATUS"],ttlMs:1000}); f.advance(1001);
 await assert.rejects(f.plane.execute({actionId:"a3",grantId:"g2",sessionId:"s1",action:"READ_STATUS"}),/ACTION_NOT_AUTHORIZED/);
});
test("action idempotency prevents duplicate side effects",async()=>{
 const f=fixture(); f.plane.issueGrant({grantId:"g1",sessionId:"s1",actions:["SEND_MESSAGE"],ttlMs:5000,maxUses:2});
 const p={actionId:"once",grantId:"g1",sessionId:"s1",action:"SEND_MESSAGE",message:"one"};
 assert.deepEqual(await f.plane.execute(p),await f.plane.execute(p)); assert.equal(f.calls.length,1);
});
test("arbitrary actions and oversized messages are rejected",async()=>{
 const f=fixture(); assert.throws(()=>f.plane.issueGrant({grantId:"g",sessionId:"s",actions:["EXECUTE_JS"],ttlMs:5000}),/ACTION_NOT_ALLOWED/);
 f.plane.issueGrant({grantId:"g2",sessionId:"s1",actions:["SEND_MESSAGE"],ttlMs:5000});
 await assert.rejects(f.plane.execute({actionId:"a",grantId:"g2",sessionId:"s1",action:"SEND_MESSAGE",message:"x".repeat(4001)}),/MESSAGE_INVALID/);
});
test("audit excludes message bodies and adapter secrets",async()=>{
 const f=fixture(); f.plane.issueGrant({grantId:"g",sessionId:"s",actions:["SEND_MESSAGE","READ_STATUS"],ttlMs:5000,maxUses:2});
 await f.plane.execute({actionId:"a1",grantId:"g",sessionId:"s",action:"SEND_MESSAGE",message:"private body"});
 await f.plane.execute({actionId:"a2",grantId:"g",sessionId:"s",action:"READ_STATUS"});
 const log=JSON.stringify(f.audits); assert.equal(log.includes("private body"),false); assert.equal(log.includes("secret"),false);
});
test("heartbeat freshness distinguishes connected and offline",()=>{
 const f=fixture(); f.plane.observeHeartbeat("s1");
 assert.equal(f.plane.inspectSession("s1",5000).state,"CONNECTED"); f.advance(6000);
 const s=f.plane.inspectSession("s1",5000); assert.equal(s.stale,true); assert.equal(s.state,"OFFLINE");
});
test("recovery applies exponential backoff and bounded attempts",async()=>{
 const f=fixture(); assert.equal((await f.plane.recoverSession("s1")).status,"REQUESTED");
 assert.equal((await f.plane.recoverSession("s1")).status,"BACKOFF"); f.advance(1000);
 assert.equal((await f.plane.recoverSession("s1")).attempts,2); f.advance(2000);
 assert.equal((await f.plane.recoverSession("s1")).status,"EXHAUSTED");
 assert.equal(f.calls.filter(x=>x[0]==="reconnect").length,2);
});
test("a fresh heartbeat resets recovery budget",async()=>{
 const f=fixture(); await f.plane.recoverSession("s1"); f.plane.observeHeartbeat("s1");
 assert.equal((await f.plane.recoverSession("s1")).attempts,1);
});
test("revocation and shutdown fail closed",async()=>{
 const f=fixture(); f.plane.issueGrant({grantId:"g",sessionId:"s",actions:["READ_STATUS"],ttlMs:5000});
 assert.equal(f.plane.revokeGrant("g"),true);
 await assert.rejects(f.plane.execute({actionId:"a",grantId:"g",sessionId:"s",action:"READ_STATUS"}),/ACTION_NOT_AUTHORIZED/);
 f.plane.stop(); assert.throws(()=>f.plane.issueGrant({grantId:"g2",sessionId:"s",actions:["READ_STATUS"],ttlMs:5000}),/CONTROL_PLANE_STOPPED/);
});
test("future heartbeat beyond clock skew is rejected",()=>{
 const f=fixture(); assert.throws(()=>f.plane.observeHeartbeat("s1",f.now()+60000),/INVALID_HEARTBEAT/);
});
