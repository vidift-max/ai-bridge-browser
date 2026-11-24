import test from "node:test";
import assert from "node:assert/strict";
import "../web/ai-room-creation.js";
const creation=globalThis.AIBridgeRoomCreation;
test("private chat payload contains exactly the authenticated identity and one peer",()=>{
 const payload=creation.buildPayload("PRIVATE",["ai-peer"],"ai-owner","private-1");
 assert.deepEqual(payload,{conversationId:"private-1",kind:"PRIVATE",memberAiIds:["ai-owner","ai-peer"]});
});
test("group chat payload deduplicates peers and always includes the authenticated identity",()=>{
 const payload=creation.buildPayload("GROUP",["ai-a","ai-b","ai-a","ai-owner"],"ai-owner","group-1");
 assert.deepEqual(payload.memberAiIds,["ai-owner","ai-a","ai-b"]);
});
test("private chat rejects zero or multiple peers",()=>{
 assert.throws(()=>creation.buildPayload("PRIVATE",[],"ai-owner","p-1"),/private_conversation_requires_one_peer/);
 assert.throws(()=>creation.buildPayload("PRIVATE",["a","b"],"ai-owner","p-2"),/private_conversation_requires_one_peer/);
});
test("group chat rejects empty and over-capacity selections",()=>{
 assert.throws(()=>creation.buildPayload("GROUP",[],"ai-owner","g-1"),/group_conversation_member_limit/);
 assert.throws(()=>creation.buildPayload("GROUP",Array.from({length:20},(_,i)=>"ai-"+i),"ai-owner","g-2"),/group_conversation_member_limit/);
});
test("payload rejects invalid kind, identity and conversation identifier",()=>{
 assert.throws(()=>creation.buildPayload("PUBLIC",["a"],"owner","id"),/invalid_conversation_kind/);
 assert.throws(()=>creation.buildPayload("PRIVATE",["a"],"","id"),/invalid_own_identity/);
 assert.throws(()=>creation.buildPayload("PRIVATE",["a"],"owner",""),/invalid_conversation_id/);
});
test("createConversation uses authenticated API and validates server response",async()=>{
 let request;
 const room=await creation.createConversation(async(path,options)=>{request={path,options};return {conversation:{conversationId:"p-3",kind:"PRIVATE",memberCount:2}}},{aiId:"owner"},"PRIVATE",["peer"],"p-3");
 assert.equal(request.path,"/v1/conversations");
 assert.equal(request.options.method,"POST");
 assert.deepEqual(JSON.parse(request.options.body),{conversationId:"p-3",kind:"PRIVATE",memberAiIds:["owner","peer"]});
 assert.equal(room.conversationId,"p-3");
});
test("createConversation rejects malformed server responses",async()=>{
 await assert.rejects(()=>creation.createConversation(async()=>({conversation:{conversationId:"wrong",kind:"PRIVATE",memberCount:2}}),{aiId:"owner"},"PRIVATE",["peer"],"p-4"),/invalid_conversation_response/);
});

test("room page exposes authenticated private and group creation controls",async()=>{
 const {readFile}=await import("node:fs/promises");
 const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
 assert.match(html,/id="conversationCreatePanel"/);
 assert.match(html,/id="conversationKind"/);
 assert.match(html,/option value="PRIVATE"/);
 assert.match(html,/option value="GROUP"/);
 assert.match(html,/id="conversationPeers" multiple/);
 assert.match(html,/AIBridgeRoomCreation\.createConversation/);
 assert.match(html,/renderConversationPeerOptions\(\)/);
 assert.doesNotMatch(html,/innerHTML/);
});
