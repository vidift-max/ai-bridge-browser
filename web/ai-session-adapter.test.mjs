import {readFile} from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";
const source=await readFile(new URL("./ai-session-adapter.js",import.meta.url),"utf8");
function fixture(options={}){
 const calls=[],audits=[];let time=10000;
 const adapter={
  async connect(meta){calls.push(["connect",meta.sessionId]);return {authenticated:true,token:"must-not-persist"};},
  async readStatus(meta){calls.push(["status",meta.sessionId]);return {state:"READY",secret:"hidden"};},
  async sendMessage(meta,msg){calls.push(["send",meta.sessionId,msg]);},
  async requestReconnect(meta){calls.push(["reconnect",meta.sessionId]);}
 };
 const context={window:{},URL};vm.runInNewContext(source,context);
 const registry=context.window.AIBridgeSessionAdapter.create({
  authorize:options.authorize||(()=>true),onAudit:e=>audits.push(e),now:()=>time
 });
 registry.registerProvider({providerId:"provider-1",allowedOrigins:["https://chat.example"],adapter});
 return {registry,calls,audits,advance(ms){time+=ms;}};
}
function handshake(id="session-1",extra={}){
 return {status:"AUTHENTICATED",sessionId:id,providerId:"provider-1",origin:"https://chat.example",
  capabilities:["READ_STATUS","SEND_MESSAGE","REQUEST_RECONNECT"],expiresAt:20000,...extra};
}
function attach(r,id="session-1",extra={}){
 return r.attachTab({sessionId:id,providerId:"provider-1",origin:"https://chat.example",
  explicitConsent:true,handshake:handshake(id),...extra});
}
test("tab registration requires explicit consent",()=>{
 const f=fixture();assert.throws(()=>f.registry.attachTab({sessionId:"s",providerId:"provider-1",
  origin:"https://chat.example",handshake:handshake("s")}),/EXPLICIT_CONSENT_REQUIRED/);
});
test("verified handshake is mandatory",()=>{
 const f=fixture();assert.throws(()=>f.registry.attachTab({sessionId:"s",providerId:"provider-1",
  origin:"https://chat.example",explicitConsent:true}),/VERIFIED_HANDSHAKE_REQUIRED/);
});
test("handshake must be bound to the exact session provider and origin",()=>{
 const f=fixture();
 assert.throws(()=>attach(f.registry,"s",{handshake:handshake("other")}),/HANDSHAKE_SESSION_BINDING_MISMATCH/);
 assert.throws(()=>attach(f.registry,"s",{handshake:handshake("s",{providerId:"provider-2"})}),/HANDSHAKE_SESSION_BINDING_MISMATCH/);
 assert.throws(()=>attach(f.registry,"s",{handshake:handshake("s",{origin:"https://evil.example"})}),/HANDSHAKE_SESSION_BINDING_MISMATCH/);
});
test("expired handshake cannot attach a tab",()=>{
 const f=fixture();assert.throws(()=>attach(f.registry,"s",{handshake:handshake("s",{expiresAt:10000})}),/HANDSHAKE_EXPIRED/);
});
test("handshake capabilities must be known unique and non-empty",()=>{
 const f=fixture();
 assert.throws(()=>attach(f.registry,"s",{handshake:handshake("s",{capabilities:[]})}),/HANDSHAKE_CAPABILITIES_INVALID/);
 assert.throws(()=>attach(f.registry,"s",{handshake:handshake("s",{capabilities:["SEND_MESSAGE","SEND_MESSAGE"]})}),/HANDSHAKE_CAPABILITIES_INVALID/);
 assert.throws(()=>attach(f.registry,"s",{handshake:handshake("s",{capabilities:["EXECUTE_JS"]})}),/HANDSHAKE_CAPABILITIES_INVALID/);
});
test("provider origin allowlist is exact and HTTPS-only",()=>{
 const f=fixture();
 assert.throws(()=>f.registry.attachTab({sessionId:"s",providerId:"provider-1",origin:"https://evil.example",
  explicitConsent:true,handshake:handshake("s",{origin:"https://evil.example"})}),/TAB_ORIGIN_NOT_ALLOWED/);
 assert.throws(()=>f.registry.attachTab({sessionId:"s",providerId:"provider-1",origin:"http://chat.example",
  explicitConsent:true,handshake:handshake("s",{origin:"http://chat.example"})}),/HTTPS_ORIGIN_REQUIRED/);
});
test("provider contract requires connect and read status capabilities",()=>{
 const context={window:{},URL};vm.runInNewContext(source,context);
 const r=context.window.AIBridgeSessionAdapter.create({});
 assert.throws(()=>r.registerProvider({providerId:"p",allowedOrigins:["https://chat.example"],adapter:{connect(){}}}),/ADAPTER_CONTRACT_INCOMPLETE/);
});
test("registration does not auto-connect a browser tab",()=>{
 const f=fixture();attach(f.registry);assert.equal(f.calls.length,0);
 assert.equal(f.registry.getSession("session-1").state,"REGISTERED");
});
test("session becomes connected only after adapter confirms authentication",async()=>{
 const f=fixture();attach(f.registry);const s=await f.registry.connect("session-1");
 assert.equal(s.state,"CONNECTED");assert.deepEqual(f.calls,[["connect","session-1"]]);
});
test("failed adapter authentication blocks the session",async()=>{
 const f=fixture();const adapter={async connect(){return {authenticated:false};},async readStatus(){return {state:"READY"};}};
 const c={window:{},URL};vm.runInNewContext(source,c);const r=c.window.AIBridgeSessionAdapter.create({});
 r.registerProvider({providerId:"p",allowedOrigins:["https://chat.example"],adapter});
 r.attachTab({sessionId:"s",providerId:"p",origin:"https://chat.example",explicitConsent:true,
  handshake:{...handshake("s"),providerId:"p"}});
 await assert.rejects(r.connect("s"),/ADAPTER_AUTHENTICATION_NOT_CONFIRMED/);
 assert.equal(r.getSession("s").state,"BLOCKED");
});
test("status reads require a connected session and a granted capability",async()=>{
 const f=fixture();attach(f.registry);await assert.rejects(f.registry.readStatus("session-1"),/SESSION_NOT_CONNECTED/);
 await f.registry.connect("session-1");const status=await f.registry.readStatus("session-1");
 assert.equal(status.state,"READY");assert.equal(Object.hasOwn(status,"secret"),false);
 const g=fixture();attach(g.registry,"s",{handshake:handshake("s",{capabilities:["SEND_MESSAGE"]})});
 await g.registry.connect("s");await assert.rejects(g.registry.readStatus("s"),/CAPABILITY_NOT_GRANTED/);
});
test("message sending requires explicit authorization and a handshake grant",async()=>{
 const f=fixture({authorize:()=>false});attach(f.registry);await f.registry.connect("session-1");
 await assert.rejects(f.registry.sendMessage("session-1","hello",{id:"grant"}),/ACTION_NOT_AUTHORIZED/);
 assert.equal(f.calls.some(x=>x[0]==="send"),false);
 const g=fixture();attach(g.registry,"s",{handshake:handshake("s",{capabilities:["READ_STATUS"]})});
 await g.registry.connect("s");await assert.rejects(g.registry.sendMessage("s","hello",{id:"grant"}),/CAPABILITY_NOT_GRANTED/);
});
test("authorized message is bounded and sent only to the registered session",async()=>{
 const f=fixture();attach(f.registry);await f.registry.connect("session-1");
 await f.registry.sendMessage("session-1","hello",{id:"grant"});
 await assert.rejects(f.registry.sendMessage("session-1","x".repeat(4001),{id:"grant"}),/MESSAGE_INVALID/);
 assert.deepEqual(f.calls.filter(x=>x[0]==="send"),[["send","session-1","hello"]]);
});
test("reconnect requires both explicit grant and provider adapter support",async()=>{
 const f=fixture();attach(f.registry,"s",{handshake:handshake("s",{capabilities:["READ_STATUS"]})});
 await f.registry.connect("s");await assert.rejects(f.registry.requestReconnect("s",{id:"grant"}),/CAPABILITY_NOT_GRANTED/);
});
test("closing during asynchronous connect cannot resurrect the removed session",async()=>{
 let release;const gate=new Promise(resolve=>{release=resolve;});
 const f=fixture();const adapter={async connect(){await gate;return {authenticated:true};},async readStatus(){return {state:"READY"};}};
 const c={window:{},URL};vm.runInNewContext(source,c);const r=c.window.AIBridgeSessionAdapter.create({now:()=>10000});
 r.registerProvider({providerId:"p",allowedOrigins:["https://chat.example"],adapter});
 r.attachTab({sessionId:"s",providerId:"p",origin:"https://chat.example",explicitConsent:true,
  handshake:{...handshake("s"),providerId:"p"}});
 const connecting=r.connect("s");assert.equal(r.close("s"),true);release();
 await assert.rejects(connecting,/SESSION_NO_LONGER_ACTIVE/);assert.equal(r.getSession("s"),null);
});
test("closing during asynchronous message send prevents a false SENT result",async()=>{
 let release;const gate=new Promise(resolve=>{release=resolve;});
 const adapter={async connect(){return {authenticated:true};},async readStatus(){return {state:"READY"};},
  async sendMessage(){await gate;},async requestReconnect(){}};
 const c={window:{},URL};vm.runInNewContext(source,c);const r=c.window.AIBridgeSessionAdapter.create({authorize:()=>true});
 r.registerProvider({providerId:"p",allowedOrigins:["https://chat.example"],adapter});
 r.attachTab({sessionId:"s",providerId:"p",origin:"https://chat.example",explicitConsent:true,
  handshake:{...handshake("s"),providerId:"p"}});
 await r.connect("s");const sending=r.sendMessage("s","hello",{id:"grant"});r.close("s");release();
 await assert.rejects(sending,/SESSION_NO_LONGER_ACTIVE/);
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
