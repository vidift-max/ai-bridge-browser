import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import {readFile} from "node:fs/promises";
const source=await readFile(new URL("./ai-conversation-loop.js",import.meta.url),"utf8");
function fixture(overrides={}){
 let context={room:{conversationId:"private-1",kind:"PRIVATE",memberAiIds:["AI-ONE","AI-TWO"]},identity:{aiId:"AI-ONE"}};
 const delivered=[],requests=[],states=[];
 let sequence=0;
 const scope={window:{},AbortController};vm.runInNewContext(source,scope);
 const loop=scope.window.AIBridgeConversationLoop.create({
  getContext:()=>context,
  respond:async request=>{requests.push(request);return {senderAiId:request.toAiId,body:"reply-"+(++sequence)};},
  deliver:async message=>{delivered.push(message);},
  onState:state=>states.push(state),
  ...overrides
 });
 return {loop,delivered,requests,states,setContext:value=>context=value};
}
test("bounded conversation alternates the two authorized AI identities and stops at its turn limit",async()=>{
 const f=fixture();const result=await f.loop.start({firstMessage:"start",maxTurns:4,runId:"bounded-1"});
 assert.equal(result.state,"IDLE");assert.equal(result.turnsCompleted,4);
 assert.deepEqual(f.requests.map(x=>x.toAiId),["AI-TWO","AI-ONE","AI-TWO","AI-ONE"]);
 assert.equal(f.delivered.length,4);assert.deepEqual(f.delivered.map(x=>x.turn),[1,2,3,4]);
 assert.equal(f.delivered.every(x=>x.conversationId==="private-1"&&x.runId==="bounded-1"),true);
});
test("default turn limit is bounded and cannot exceed the hard maximum",async()=>{
 const f=fixture();await f.loop.start({firstMessage:"go"});
 assert.equal(f.requests.length,6);
 await assert.rejects(f.loop.start({firstMessage:"go",maxTurns:21}),/INVALID_MAX_TURNS/);
 await assert.rejects(f.loop.start({firstMessage:"go",maxTurns:1}),/INVALID_MAX_TURNS/);
});
test("stop interrupts a pending responder and prevents delivery after stop",async()=>{
 let release;const wait=new Promise(resolve=>{release=resolve;});
 const f=fixture({respond:async request=>{await wait;return {senderAiId:request.toAiId,body:"late"};}});
 const running=f.loop.start({firstMessage:"start",maxTurns:10});
 await new Promise(resolve=>setImmediate(resolve));
 const stopped=f.loop.stop();assert.equal(stopped.stopRequested,true);
 release();const result=await running;
 assert.equal(result.turnsCompleted,0);assert.equal(f.delivered.length,0);
 assert.equal(result.state,"STOPPED");
});
test("second run cannot overlap an active conversation",async()=>{
 let release;const wait=new Promise(resolve=>{release=resolve;});
 const f=fixture({respond:async request=>{await wait;return {senderAiId:request.toAiId,body:"reply"};}});
 const running=f.loop.start({firstMessage:"start",maxTurns:2});
 await new Promise(resolve=>setImmediate(resolve));
 await assert.rejects(f.loop.start({firstMessage:"another",maxTurns:2}),/CONVERSATION_LOOP_ALREADY_RUNNING/);
 f.loop.stop();release();await running;
});
test("only an authenticated two-member private room can start a loop",async()=>{
 const f=fixture();f.setContext({room:{conversationId:"group",kind:"GROUP",memberAiIds:["AI-ONE","AI-TWO"]},identity:{aiId:"AI-ONE"}});
 await assert.rejects(f.loop.start({firstMessage:"go"}),/PRIVATE_TWO_MEMBER_ROOM_REQUIRED/);
 f.setContext({room:{conversationId:"private",kind:"PRIVATE",memberAiIds:["AI-ONE","AI-TWO","AI-THREE"]},identity:{aiId:"AI-ONE"}});
 await assert.rejects(f.loop.start({firstMessage:"go"}),/PRIVATE_TWO_MEMBER_ROOM_REQUIRED/);
 f.setContext({room:{conversationId:"private",kind:"PRIVATE",memberAiIds:["AI-TWO","AI-THREE"]},identity:{aiId:"AI-ONE"}});
 await assert.rejects(f.loop.start({firstMessage:"go"}),/PRIVATE_TWO_MEMBER_ROOM_REQUIRED/);
 assert.equal(f.requests.length,0);
});
test("loop rejects blank and oversized initial prompts before calling agents",async()=>{
 const f=fixture();
 await assert.rejects(f.loop.start({firstMessage:"   "}),/INVALID_FIRST_MESSAGE/);
 await assert.rejects(f.loop.start({firstMessage:"x".repeat(5001)}),/INVALID_FIRST_MESSAGE/);
 assert.equal(f.requests.length,0);
});
test("loop rejects forged agent identity and empty or oversized responses",async()=>{
 for(const response of [
  {senderAiId:"AI-OUTSIDER",body:"forged"},
  {senderAiId:"AI-TWO",body:"  "},
  {senderAiId:"AI-TWO",body:"x".repeat(5001)}
 ]){
  const f=fixture({respond:async()=>response});
  await assert.rejects(f.loop.start({firstMessage:"go",maxTurns:2}),/INVALID_AGENT_RESPONSE/);
  assert.equal(f.delivered.length,0);
 }
});
test("loop aborts when the active room or identity changes mid-run",async()=>{
 let f;
 f=fixture({respond:async request=>{
  f.setContext({room:{conversationId:"other",kind:"PRIVATE",memberAiIds:["AI-ONE","AI-TWO"]},identity:{aiId:"AI-ONE"}});
  return {senderAiId:request.toAiId,body:"reply"};
 }});
 await assert.rejects(f.loop.start({firstMessage:"go",maxTurns:3}),/CONVERSATION_CONTEXT_CHANGED/);
 assert.equal(f.delivered.length,0);
});
test("loop exposes observable running, stopped, and completed states",async()=>{
 const f=fixture();const unsub=f.loop.subscribe(state=>f.states.push(state));
 await f.loop.start({firstMessage:"go",maxTurns:2});unsub();
 assert.equal(f.states.some(state=>state.state==="RUNNING"),true);
 assert.equal(f.states.at(-1).state,"IDLE");
 assert.equal(f.loop.snapshot().turnsCompleted,2);
});
test("provider errors stop the loop and do not create phantom deliveries",async()=>{
 const f=fixture({respond:async()=>{throw new Error("provider_unavailable");}});
 await assert.rejects(f.loop.start({firstMessage:"go",maxTurns:3}),/provider_unavailable/);
 assert.equal(f.loop.snapshot().running,false);assert.equal(f.delivered.length,0);
});
test("conversation controller exports a bounded default and maximum",()=>{
 const scope={window:{},AbortController};vm.runInNewContext(source,scope);
 assert.equal(scope.window.AIBridgeConversationLoop.DEFAULT_TURNS,6);
 assert.equal(scope.window.AIBridgeConversationLoop.MAX_TURNS,20);
});
