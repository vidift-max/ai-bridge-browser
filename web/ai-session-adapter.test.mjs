import {readFile} from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";
const source=await readFile(new URL("./ai-session-adapter.js",import.meta.url),"utf8");
function fixture(options={}){
 const calls=[],audits=[];const adapter={
  async connect(meta){calls.push(["connect",meta.sessionId]);return {authenticated:true,token:"must-not-persist"};},
  async readStatus(meta){calls.push(["status",meta.sessionId]);return {state:"READY",secret:"hidden"};},
  async sendMessage(meta,msg){calls.push(["send",meta.sessionId,msg]);},
  async requestReconnect(meta){calls.push(["reconnect",meta.sessionId]);}
 };
 const context={window:{},URL};vm.runInNewContext(source,context);
 const registry=context.window.AIBridgeSessionAdapter.create({
  authorize:options.authorize||(()=>true),onAudit:e=>audits.push(e)
 });
 registry.registerProvider({providerId:"provider-1",allowedOrigins:["https://chat.example"],adapter});
 return {registry,calls,audits};
}
function attach(r,id="session-1",extra={}){return r.attachTab({sessionId:id,providerId:"provider-1",origin:"https://chat.example",explicitConsent:true,...extra});}
test("tab registration requires explicit consent",()=>{
 const f=fixture();assert.throws(()=>f.registry.attachTab({sessionId:"s",providerId:"provider-1",origin:"https://chat.example"}),/EXPLICIT_CONSENT_REQUIRED/);
});
test("provider origin allowlist is exact and HTTPS-only",()=>{
 const f=fixture();assert.throws(()=>f.registry.attachTab({sessionId:"s",providerId:"provider-1",origin:"https://evil.example",explicitConsent:true}),/TAB_ORIGIN_NOT_ALLOWED/);
 assert.throws(()=>f.registry.attachTab({sessionId:"s",providerId:"provider-1",origin:"http://chat.example",explicitConsent:true}),/HTTPS_ORIGIN_REQUIRED/);
});
test("provider contract requires connect and read status capabilities",()=>{
 const context={window:{}};vm.runInNewContext(source,context);
 const r=context.window.AIBridgeSessionAdapter.create({});
 assert.throws(()=>r.registerProvider({providerId:"p",allowedOrigins:["https://chat.example"],adapter:{connect(){}}}),/ADAPTER_CONTRACT_INCOMPLETE/);
});
test("registration does not auto-connect a browser tab",()=>{
 const f=fixture();attach(f.registry);assert.equal(f.calls.length,0);assert.equal(f.registry.getSession("session-1").state,"REGISTERED");
});
test("session becomes connected only after adapter confirms authentication",async()=>{
 const f=fixture();attach(f.registry);const s=await f.registry.connect("session-1");
 assert.equal(s.state,"CONNECTED");assert.deepEqual(f.calls,[["connect","session-1"]]);
});
test("failed authentication blocks the session",async()=>{
 const f=fixture();const adapter={async connect(){return {authenticated:false};},async readStatus(){return {state:"READY"};}};
 const c={window:{},URL};vm.runInNewContext(source,c);const r=c.window.AIBridgeSessionAdapter.create({});
 r.registerProvider({providerId:"p",allowedOrigins:["https://chat.example"],adapter});
 r.attachTab({sessionId:"s",providerId:"p",origin:"https://chat.example",explicitConsent:true});
 await assert.rejects(r.connect("s"),/ADAPTER_AUTHENTICATION_NOT_CONFIRMED/);assert.equal(r.getSession("s").state,"BLOCKED");
});
test("status reads require a connected session and return minimal data",async()=>{
 const f=fixture();attach(f.registry);await assert.rejects(f.registry.readStatus("session-1"),/SESSION_NOT_CONNECTED/);
 await f.registry.connect("session-1");const status=await f.registry.readStatus("session-1");
 assert.equal(status.state,"READY");assert.equal(Object.hasOwn(status,"secret"),false);
});
test("message sending requires explicit authorization and adapter capability",async()=>{
 const f=fixture({authorize:()=>false});attach(f.registry);await f.registry.connect("session-1");
 await assert.rejects(f.registry.sendMessage("session-1","hello",{id:"grant"}),/ACTION_NOT_AUTHORIZED/);
 assert.equal(f.calls.some(x=>x[0]==="send"),false);
});
test("authorized message is bounded and sent only to the registered session",async()=>{
 const f=fixture();attach(f.registry);await f.registry.connect("session-1");
 await f.registry.sendMessage("session-1","hello",{id:"grant"});
 await assert.rejects(f.registry.sendMessage("session-1","x".repeat(4001),{id:"grant"}),/MESSAGE_INVALID/);
 assert.deepEqual(f.calls.filter(x=>x[0]==="send"),[["send","session-1","hello"]]);
});
test("audit records and session metadata never contain adapter credentials or message bodies",async()=>{
 const f=fixture();attach(f.registry);await f.registry.connect("session-1");
 await f.registry.sendMessage("session-1","private body",{id:"grant"});
 const text=JSON.stringify({audit:f.audits,sessions:f.registry.list()});
 assert.equal(text.includes("must-not-persist"),false);assert.equal(text.includes("private body"),false);
});
test("closing and stopping remove sessions and prevent further registration",async()=>{
 const f=fixture();attach(f.registry);await f.registry.connect("session-1");
 assert.equal(f.registry.close("session-1"),true);assert.equal(f.registry.getSession("session-1"),null);
 f.registry.stop();assert.throws(()=>attach(f.registry,"session-2"),/REGISTRY_STOPPED/);
});
