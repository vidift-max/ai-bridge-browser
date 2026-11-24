import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import {readFile} from "node:fs/promises";
const source=await readFile(new URL("./ai-room-ui-messenger.js",import.meta.url),"utf8");
function fixture(){
 const calls=[],rendered=[];
 let ctx={room:{conversationId:"room-a",memberAiIds:["AI-GPT6","AI-CLAUDE","AI-GEMINI"]},identity:{aiId:"AI-GPT6"}};
 const api=async(path,options={})=>{calls.push({path,options});if(path==="/v1/messages")return {sequence:9};if(path.includes("/messages?"))return {messages:[]};return {ok:true};};
 const scope={window:{},crypto:{randomUUID:()=>"uuid-1"},URLSearchParams};
 vm.runInNewContext(source,scope);
 const messenger=scope.window.AIBridgeRoomUIMessenger.create({api,getContext:()=>ctx,onMessage:(m,mine)=>rendered.push({m,mine})});
 return {messenger,calls,rendered,setContext:v=>ctx=v,api};
}
test("UI messenger sends only to other members of the selected room and renders after server success",async()=>{
 const f=fixture();await f.messenger.send("  hello  ",{messageId:"m1",clientRequestId:"c1"});
 const call=f.calls[0];assert.equal(call.path,"/v1/messages");
 const payload=JSON.parse(call.options.body);assert.equal(payload.conversationId,"room-a");
 assert.deepEqual(Array.from(payload.recipientAiIds),["AI-CLAUDE","AI-GEMINI"]);
 assert.equal(payload.body,"hello");assert.equal(f.rendered.length,1);assert.equal(f.rendered[0].mine,true);
});
test("UI messenger refuses outsider, blank and oversized sends before network access",async()=>{
 const f=fixture();f.setContext({room:{conversationId:"room-a",memberAiIds:["AI-CLAUDE","AI-GEMINI"]},identity:{aiId:"AI-OUTSIDER"}});
 await assert.rejects(f.messenger.send("hello"),/ROOM_UI_MEMBERSHIP_REQUIRED/);
 f.setContext({room:{conversationId:"room-a",memberAiIds:["AI-GPT6","AI-CLAUDE"]},identity:{aiId:"AI-GPT6"}});
 await assert.rejects(f.messenger.send("  "),/INVALID_MESSAGE_BODY/);
 await assert.rejects(f.messenger.send("x".repeat(5001)),/INVALID_MESSAGE_BODY/);
 assert.equal(f.calls.length,0);
});
test("UI messenger acknowledges before rendering and advances cursor only after ACK",async()=>{
 const f=fixture();let acked=false;
 f.api=async(path)=>{if(path.includes("/messages?"))return {messages:[{messageId:"m1",conversationId:"room-a",senderAiId:"AI-CLAUDE",body:"incoming",sequence:4}]};if(path.endsWith("/ack")){acked=true;return {ok:true};}return {};};
 const messenger=f.messenger;
 // Recreate with instrumented API to observe ACK/render ordering.
 const scope={window:{},crypto:{randomUUID:()=>"id"}};
 vm.runInNewContext(source,scope);
 const m=scope.window.AIBridgeRoomUIMessenger.create({api:f.api,getContext:()=>({room:{conversationId:"room-a",memberAiIds:["AI-GPT6","AI-CLAUDE"]},identity:{aiId:"AI-GPT6"}}),onMessage:()=>{assert.equal(acked,true);}});
 assert.equal(await m.load(),4);assert.equal(m.getCursor(),4);
});
test("UI messenger rejects malformed server batches and leaves cursor unchanged",async()=>{
 const f=fixture();f.api=async()=>({messages:[{messageId:"bad",conversationId:"other",senderAiId:"AI-X",body:"x",sequence:1}]});
 const scope={window:{}};vm.runInNewContext(source,scope);
 const m=scope.window.AIBridgeRoomUIMessenger.create({api:f.api,getContext:()=>({room:{conversationId:"room-a",memberAiIds:["AI-GPT6","AI-X"]},identity:{aiId:"AI-GPT6"}}),onMessage:()=>{}});
 await assert.rejects(m.load(),/ROOM_UI_MESSAGE_INVALID/);assert.equal(m.getCursor(),0);
});
test("UI messenger deduplicates display while acknowledging repeated delivery",async()=>{
 const f=fixture();let batch=[{messageId:"m1",conversationId:"room-a",senderAiId:"AI-CLAUDE",body:"hello",sequence:1}],acks=0;
 const api=async path=>{if(path.includes("/messages?"))return {messages:batch};if(path.endsWith("/ack")){acks++;return {};}return {};};
 const scope={window:{}};vm.runInNewContext(source,scope);let count=0;
 const m=scope.window.AIBridgeRoomUIMessenger.create({api,getContext:()=>({room:{conversationId:"room-a",memberAiIds:["AI-GPT6","AI-CLAUDE"]},identity:{aiId:"AI-GPT6"}}),onMessage:()=>count++});
 await m.load();m.reset();await m.load();assert.equal(count,1);assert.equal(acks,2);
});
