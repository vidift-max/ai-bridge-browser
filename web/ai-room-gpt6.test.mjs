import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import {readFile} from "node:fs/promises";
const source=await readFile(new URL("./ai-room-gpt6.js",import.meta.url),"utf8");
function fixture(){
 const calls=[],scope={window:{}};vm.runInNewContext(source,scope);
 const context={room:{conversationId:"room-main",memberAiIds:["AI-USER","AI-GPT6","AI-CLAUDE"]},identity:{aiId:"AI-USER"}};
 const api=async(path,options)=>{calls.push({path,options});return {userMessage:{conversationId:"room-main",senderAiId:"AI-USER"},assistantMessage:{conversationId:"room-main",senderAiId:"AI-GPT6",body:"Olá!",sequence:2}}};
 return {bridge:scope.window.AIBridgeRoomGPT6.create({api,getContext:()=>context}),calls,context,api};
}
test("primary room bridge sends user input to the GPT-6 room endpoint",async()=>{
 const f=fixture(),result=await f.bridge.respond(" oi ","request-1234");
 assert.equal(f.calls.length,1);assert.equal(f.calls[0].path,"/v1/gpt6/room/respond");
 assert.deepEqual(JSON.parse(f.calls[0].options.body),{conversationId:"room-main",message:"oi",clientRequestId:"request-1234"});
 assert.equal(result.assistantMessage.senderAiId,"AI-GPT6");
});
test("bridge refuses rooms without explicit GPT-6 membership",async()=>{
 const f=fixture();f.context.room.memberAiIds=["AI-USER","AI-CLAUDE"];
 await assert.rejects(f.bridge.respond("oi","request-1234"),/ROOM_GPT6_NOT_SELECTED/);assert.equal(f.calls.length,0);
});
test("bridge rejects malformed responses and invalid request IDs",async()=>{
 const f=fixture();f.api=async()=>({userMessage:{senderAiId:"AI-USER",conversationId:"room-main"},assistantMessage:{senderAiId:"AI-OTHER",conversationId:"room-main",body:"fake",sequence:2}});
 const scope={window:{}};vm.runInNewContext(source,scope);
 const bridge=scope.window.AIBridgeRoomGPT6.create({api:f.api,getContext:()=>f.context});
 await assert.rejects(bridge.respond("oi","request-1234"),/ROOM_GPT6_RESPONSE_INVALID/);
 await assert.rejects(bridge.respond("oi","bad id"),/ROOM_GPT6_INVALID_REQUEST_ID/);
});
test("Rooms page uses GPT-6 bridge in the existing composer and exposes opt-in group membership",async()=>{
 const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
 assert.match(html,/<script src="\/ai-room-gpt6\.js"><\/script>/);
 assert.match(html,/id="includeGpt6InGroup"/);assert.match(html,/AIBridgeRoomGPT6\.create/);
 assert.match(html,/memberAiIds\.includes\('AI-GPT6'\)/);assert.match(html,/await loadMessages\(\)/);
});
