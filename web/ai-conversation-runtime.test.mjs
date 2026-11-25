import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import {readFile} from "node:fs/promises";
const adapterSource=await readFile(new URL("./ai-agent-adapter.js",import.meta.url),"utf8");
const loopSource=await readFile(new URL("./ai-conversation-loop.js",import.meta.url),"utf8");
const runtimeSource=await readFile(new URL("./ai-conversation-runtime.js",import.meta.url),"utf8");
function fixture(){
 const calls=[],shown=[];
 const scope={window:{}};
 vm.runInNewContext(adapterSource,scope);vm.runInNewContext(loopSource,scope);vm.runInNewContext(runtimeSource,scope);
 const getContext=()=>({room:{conversationId:"private-1",kind:"PRIVATE",memberAiIds:["AI-ONE","AI-TWO"]},identity:{aiId:"AI-ONE"}});
 const runtime=scope.window.AIBridgeConversationRuntime.create({
  getContext,
  requestAgent:async request=>{calls.push(request);return {conversationId:request.conversationId,agentId:request.agentId,body:"reply-"+request.turn,attestation:"proof"};},
  verifyAttestation:async result=>result.attestation==="proof",
  onMessage:async message=>shown.push(message)
 });
 return {runtime,calls,shown};
}
test("runtime composes attested agent responses with bounded controller",async()=>{
 const f=fixture();const result=await f.runtime.start({firstMessage:"start",maxTurns:4,runId:"runtime-1"});
 assert.equal(result.turnsCompleted,4);
 assert.deepEqual(f.calls.map(x=>x.agentId),["AI-TWO","AI-ONE","AI-TWO","AI-ONE"]);
 assert.equal(f.shown.length,4);
 assert.equal(f.shown.every(x=>x.conversationId==="private-1"&&x.runId==="runtime-1"),true);
});
test("runtime fails closed when provider attestation is invalid",async()=>{
 const scope={window:{}};vm.runInNewContext(adapterSource,scope);vm.runInNewContext(loopSource,scope);vm.runInNewContext(runtimeSource,scope);
 const runtime=scope.window.AIBridgeConversationRuntime.create({
  getContext:()=>({room:{conversationId:"p",kind:"PRIVATE",memberAiIds:["A","B"]},identity:{aiId:"A"}}),
  requestAgent:async r=>({conversationId:r.conversationId,agentId:r.agentId,body:"forged",attestation:"bad"}),
  verifyAttestation:async()=>false,onMessage:async()=>{throw new Error("must_not_render");}
 });
 await assert.rejects(runtime.start({firstMessage:"start",maxTurns:2}),/AI_AGENT_ATTESTATION_INVALID/);
 assert.equal(runtime.snapshot().turnsCompleted,0);
});
