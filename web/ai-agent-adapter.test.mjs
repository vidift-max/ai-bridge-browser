import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import {readFile} from "node:fs/promises";
const source=await readFile(new URL("./ai-agent-adapter.js",import.meta.url),"utf8");
function fixture(overrides={}){
 let context={room:{conversationId:"private-1",kind:"PRIVATE",memberAiIds:["AI-ONE","AI-TWO"]},identity:{aiId:"AI-ONE"}};
 const requests=[],messages=[];
 const scope={window:{}};vm.runInNewContext(source,scope);
 const adapter=scope.window.AIBridgeAuthenticatedAgentAdapter.create({
  getContext:()=>context,
  requestAgent:async request=>{requests.push(request);return {conversationId:request.conversationId,agentId:request.agentId,body:"verified reply",attestation:"signed-proof"};},
  verifyAttestation:async result=>result.attestation==="signed-proof",
  onMessage:async message=>messages.push(message),...overrides
 });
 return {adapter,requests,messages,setContext:value=>context=value};
}
const request={conversationId:"private-1",fromAiId:"AI-ONE",toAiId:"AI-TWO",prompt:"hello",turn:1,maxTurns:4};
test("adapter delegates to selected peer and accepts only verified server attestation",async()=>{
 const f=fixture();const result=await f.adapter.respond(request);
 assert.equal(f.requests[0].agentId,"AI-TWO");assert.equal(result.senderAiId,"AI-TWO");
 assert.equal(result.body,"verified reply");
});
test("adapter rejects forged or missing attestation",async()=>{
 const f=fixture({verifyAttestation:async()=>false});
 await assert.rejects(f.adapter.respond(request),/AI_AGENT_ATTESTATION_INVALID/);
});
test("adapter never accepts identity or room supplied outside current membership",async()=>{
 const f=fixture();
 await assert.rejects(f.adapter.respond({...request,toAiId:"AI-OUTSIDER"}),/AI_AGENT_REQUEST_INVALID/);
 await assert.rejects(f.adapter.respond({...request,fromAiId:"AI-OUTSIDER"}),/AI_AGENT_REQUEST_INVALID/);
});
test("adapter fails closed outside an exact two-member private room",async()=>{
 const f=fixture();f.setContext({room:{conversationId:"group",kind:"GROUP",memberAiIds:["AI-ONE","AI-TWO"]},identity:{aiId:"AI-ONE"}});
 await assert.rejects(f.adapter.respond({...request,conversationId:"group"}),/AI_AGENT_PRIVATE_MEMBERSHIP_REQUIRED/);
});
test("adapter rejects context changes while provider is responding",async()=>{
 let f;f=fixture({requestAgent:async r=>{f.setContext({room:{conversationId:"other",kind:"PRIVATE",memberAiIds:["AI-ONE","AI-TWO"]},identity:{aiId:"AI-ONE"}});return {conversationId:r.conversationId,agentId:r.agentId,body:"late",attestation:"signed-proof"};}});
 await assert.rejects(f.adapter.respond(request),/AI_AGENT_CONTEXT_CHANGED/);
});
test("display callback accepts only current private-room participants and local recipient",async()=>{
 const f=fixture();await f.adapter.deliver({conversationId:"private-1",senderAiId:"AI-TWO",recipientAiId:"AI-ONE",body:"hello",turn:1});
 assert.equal(f.messages.length,1);
 await assert.rejects(f.adapter.deliver({conversationId:"private-1",senderAiId:"AI-OUTSIDER",recipientAiId:"AI-ONE",body:"bad",turn:2}),/AI_AGENT_DISPLAY_MESSAGE_INVALID/);
});
test("adapter bounds prompt and response lengths",async()=>{
 const f=fixture();
 await assert.rejects(f.adapter.respond({...request,prompt:"x".repeat(5001)}),/AI_AGENT_REQUEST_INVALID/);
 const bad=fixture({requestAgent:async r=>({conversationId:r.conversationId,agentId:r.agentId,body:"x".repeat(5001),attestation:"signed-proof"})});
 await assert.rejects(bad.adapter.respond(request),/AI_AGENT_ATTESTATION_INVALID/);
});
test("provider errors propagate without fabricated messages",async()=>{
 const f=fixture({requestAgent:async()=>{throw new Error("provider_offline");}});
 await assert.rejects(f.adapter.respond(request),/provider_offline/);
 assert.equal(f.messages.length,0);
});
