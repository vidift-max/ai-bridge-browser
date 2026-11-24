import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import vm from "node:vm";
const admissionSource=await readFile(new URL("./ai-room-admission.js",import.meta.url),"utf8");
const messengerSource=await readFile(new URL("./ai-room-messenger.js",import.meta.url),"utf8");
function fixture(){
 const sessions=new Map([
  ["s0",{sessionId:"s0",providerId:"openai",state:"CONNECTED"}],
  ["s1",{sessionId:"s1",providerId:"anthropic",state:"CONNECTED"}],
  ["s2",{sessionId:"s2",providerId:"google",state:"CONNECTED"}],\n  ["s3",{sessionId:"s3",providerId:"google",state:"CONNECTED"}]
 ]);
 const context={window:{},URL,crypto:{randomUUID:()=> "generated-id"}};
 vm.runInNewContext(admissionSource,context);
 const admission=context.window.AIBridgeRoomAdmission.create({sessions:{getSession:id=>sessions.get(id)||null},now:()=>1000,maxParticipants:6});
 admission.createRoom({roomId:"room",coordinatorAiId:"AI-GPT-6",coordinatorSessionId:"s0"});
 admission.issueInvitation({roomId:"room",invitationId:"i1",aiId:"AI-CLAUDE",role:"PARTICIPANT",expiresAt:5000,issuedByAiId:"AI-GPT-6"});
 admission.admit({roomId:"room",invitationId:"i1",aiId:"AI-CLAUDE",sessionId:"s1"});
 admission.issueInvitation({roomId:"room",invitationId:"i2",aiId:"AI-GEMINI",role:"PARTICIPANT",expiresAt:5000,issuedByAiId:"AI-GPT-6"});
 admission.admit({roomId:"room",invitationId:"i2",aiId:"AI-GEMINI",sessionId:"s2"});
 const sent=[],acked=[],delivered=[];
 vm.runInNewContext(messengerSource,context);
 const messenger=context.window.AIBridgeRoomMessenger.create({admission,
  sendTransport:async payload=>{sent.push(payload);return {sequence:sent.length};},
  acknowledge:async value=>acked.push(value),
  deliver:async value=>delivered.push(value)});
 return {admission,messenger,sent,acked,delivered,sessions};
}
test("outbound payload is authorized and targets only active writable room members",()=>{
 const f=fixture();const p=f.messenger.createPayload({roomId:"room",aiId:"AI-CLAUDE",sessionId:"s1",body:" hello ",messageId:"m1",clientRequestId:"c1"});
 assert.equal(p.senderAiId,"AI-CLAUDE");assert.deepEqual(Array.from(p.recipientAiIds),["AI-GPT-6","AI-GEMINI"]);assert.equal(p.body,"hello");
});
test("outbound message rejects a mismatched session and non-member",()=>{
 const f=fixture();
 assert.throws(()=>f.messenger.createPayload({roomId:"room",aiId:"AI-CLAUDE",sessionId:"s2",body:"x"}),/ROOM_MEMBERSHIP_REQUIRED/);
 assert.throws(()=>f.messenger.createPayload({roomId:"room",aiId:"AI-OTHER",sessionId:"s2",body:"x"}),/ROOM_MEMBERSHIP_REQUIRED/);
});
test("outbound send rechecks authorization after transport completes",async()=>{
 const f=fixture();let resolve;
 const pending=new Promise(r=>resolve=r);
 const messenger=f.messenger;
 const sending=messenger.send({roomId:"room",aiId:"AI-CLAUDE",sessionId:"s1",body:"hello"});
 f.admission.revoke({roomId:"room",byAiId:"AI-GPT-6",aiId:"AI-CLAUDE"});
 await assert.rejects(sending,/ROOM_MEMBERSHIP_REQUIRED/);
 resolve?.();
});
test("inbound delivery derives sender session from authoritative membership, then acknowledges",async()=>{
 const f=fixture();const result=await f.messenger.receive({localAiId:"AI-GPT-6",localSessionId:"s0",message:{
  messageId:"m1",roomId:"room",senderAiId:"AI-CLAUDE",senderSessionId:"forged",recipientAiIds:["AI-GPT-6"],body:"hello",sequence:1
 }});
 assert.equal(result.status,"DELIVERED_AND_ACKNOWLEDGED");assert.equal(f.delivered.length,1);assert.equal(f.acked.length,1);
});
test("inbound rejects spoofed sender, unauthorized recipient, and local session mismatch",async()=>{
 const f=fixture();
 await assert.rejects(f.messenger.receive({localAiId:"AI-GPT-6",localSessionId:"s0",message:{messageId:"m",roomId:"room",senderAiId:"AI-OUTSIDER",recipientAiIds:["AI-GPT-6"],body:"x",sequence:1}}),/ROOM_MEMBERSHIP_REQUIRED/);
 await assert.rejects(f.messenger.receive({localAiId:"AI-GEMINI",localSessionId:"s2",message:{messageId:"m2",roomId:"room",senderAiId:"AI-CLAUDE",recipientAiIds:["AI-GPT-6"],body:"x",sequence:2}}),/INBOUND_MESSAGE_INVALID/);
 await assert.rejects(f.messenger.receive({localAiId:"AI-GPT-6",localSessionId:"s1",message:{messageId:"m3",roomId:"room",senderAiId:"AI-CLAUDE",recipientAiIds:["AI-GPT-6"],body:"x",sequence:3}}),/LOCAL_ROOM_MEMBERSHIP_REQUIRED/);
});
test("observer cannot send and cannot be accepted as a sender",async()=>{
 const f=fixture();
 f.admission.issueInvitation({roomId:"room",invitationId:"obs",aiId:"AI-OBSERVER",role:"OBSERVER",expiresAt:5000,issuedByAiId:"AI-GPT-6"});
 f.admission.admit({roomId:"room",invitationId:"obs",aiId:"AI-OBSERVER",sessionId:"s3"});
 assert.throws(()=>f.messenger.createPayload({roomId:"room",aiId:"AI-OBSERVER",sessionId:"s3",body:"x"}),/ROOM_ROLE_READ_ONLY/);
 await assert.rejects(f.messenger.receive({localAiId:"AI-GPT-6",localSessionId:"s0",message:{messageId:"obs-m",roomId:"room",senderAiId:"AI-OBSERVER",recipientAiIds:["AI-GPT-6"],body:"x",sequence:1}}),/SENDER_ROLE_READ_ONLY/);
});
test("revoked sender or recipient cannot send or receive",async()=>{
 const f=fixture();f.admission.revoke({roomId:"room",byAiId:"AI-GPT-6",aiId:"AI-CLAUDE"});
 assert.throws(()=>f.messenger.createPayload({roomId:"room",aiId:"AI-CLAUDE",sessionId:"s1",body:"x"}),/ROOM_MEMBERSHIP_REQUIRED/);
 await assert.rejects(f.messenger.receive({localAiId:"AI-CLAUDE",localSessionId:"s1",message:{messageId:"r",roomId:"room",senderAiId:"AI-GEMINI",recipientAiIds:["AI-CLAUDE"],body:"x",sequence:1}}),/LOCAL_ROOM_MEMBERSHIP_REQUIRED/);
});
test("delivery failure never acknowledges and permits safe retry",async()=>{
 const f=fixture();let fail=true;
 const messengerContext={window:{},URL,crypto:{randomUUID:()=>"id"}};vm.runInNewContext(messengerSource,messengerContext);
 const m=messengerContext.window.AIBridgeRoomMessenger.create({admission:f.admission,
  sendTransport:async()=>({sequence:1}),acknowledge:async v=>f.acked.push(v),
  deliver:async v=>{if(fail)throw new Error("render_failed");f.delivered.push(v);}});
 const msg={messageId:"retry",roomId:"room",senderAiId:"AI-CLAUDE",recipientAiIds:["AI-GPT-6"],body:"hello",sequence:9};
 await assert.rejects(m.receive({localAiId:"AI-GPT-6",localSessionId:"s0",message:msg}),/render_failed/);
 assert.equal(f.acked.length,0);fail=false;
 assert.equal((await m.receive({localAiId:"AI-GPT-6",localSessionId:"s0",message:msg})).status,"DELIVERED_AND_ACKNOWLEDGED");
});
test("duplicate delivery is acknowledged idempotently without redelivery",async()=>{
 const f=fixture();const msg={messageId:"dup",roomId:"room",senderAiId:"AI-CLAUDE",recipientAiIds:["AI-GPT-6"],body:"hello",sequence:4};
 await f.messenger.receive({localAiId:"AI-GPT-6",localSessionId:"s0",message:msg});
 const result=await f.messenger.receive({localAiId:"AI-GPT-6",localSessionId:"s0",message:msg});
 assert.equal(result.status,"DUPLICATE_ACKNOWLEDGED");assert.equal(f.delivered.length,1);assert.equal(f.acked.length,2);
});
test("room closure blocks subsequent outbound and inbound messages",async()=>{
 const f=fixture();f.admission.closeRoom({roomId:"room",byAiId:"AI-GPT-6"});
 assert.throws(()=>f.messenger.createPayload({roomId:"room",aiId:"AI-CLAUDE",sessionId:"s1",body:"x"}),/ROOM_NOT_ACTIVE/);
});
test("message body and sequence are strictly bounded",async()=>{
 const f=fixture();
 assert.throws(()=>f.messenger.createPayload({roomId:"room",aiId:"AI-CLAUDE",sessionId:"s1",body:" "}),/INVALID_MESSAGE_BODY/);
 assert.throws(()=>f.messenger.createPayload({roomId:"room",aiId:"AI-CLAUDE",sessionId:"s1",body:"x".repeat(5001)}),/INVALID_MESSAGE_BODY/);
 await assert.rejects(f.messenger.receive({localAiId:"AI-GPT-6",localSessionId:"s0",message:{messageId:"bad",roomId:"room",senderAiId:"AI-CLAUDE",recipientAiIds:["AI-GPT-6"],body:"x",sequence:Number.MAX_SAFE_INTEGER+1}}),/INBOUND_MESSAGE_INVALID/);
});
test("source documents room-scoped authorization and long-poll transport boundary",async()=>{
 const doc=await readFile(new URL("../docs/MISSION_52_AUTHORIZED_MULTI_AI_MESSAGING.md",import.meta.url),"utf8");
 assert.match(doc,/HTTP Long Poll remains the only enabled realtime transport/);
 assert.match(doc,/Acknowledgement occurs only after successful local delivery/);
});

test("read-only observer may receive and acknowledge but cannot send",async()=>{
 const f=fixture();
 f.admission.issueInvitation({roomId:"room",invitationId:"obs2",aiId:"AI-OBSERVER",role:"OBSERVER",expiresAt:5000,issuedByAiId:"AI-GPT-6"});
 f.admission.admit({roomId:"room",invitationId:"obs2",aiId:"AI-OBSERVER",sessionId:"s3"});
 const result=await f.messenger.receive({localAiId:"AI-OBSERVER",localSessionId:"s2",message:{
  messageId:"to-observer",roomId:"room",senderAiId:"AI-CLAUDE",recipientAiIds:["AI-OBSERVER"],body:"read-only",sequence:22
 }});
 assert.equal(result.status,"DELIVERED_AND_ACKNOWLEDGED");
 assert.equal(f.delivered.length,1);assert.equal(f.acked.length,1);
});
test("inbound recipients must be unique valid identities",async()=>{
 const f=fixture();
 await assert.rejects(f.messenger.receive({localAiId:"AI-GPT-6",localSessionId:"s0",message:{
  messageId:"bad-recipient",roomId:"room",senderAiId:"AI-CLAUDE",recipientAiIds:["AI-GPT-6","AI-GPT-6"],body:"x",sequence:2
 }}),/INBOUND_MESSAGE_INVALID/);
});

test("outbound messages include active observers as read-only recipients",()=>{
 const f=fixture();
 f.admission.issueInvitation({roomId:"room",invitationId:"obs3",aiId:"AI-OBSERVER",role:"OBSERVER",expiresAt:5000,issuedByAiId:"AI-GPT-6"});
 f.admission.admit({roomId:"room",invitationId:"obs3",aiId:"AI-OBSERVER",sessionId:"s3"});
 const payload=f.messenger.createPayload({roomId:"room",aiId:"AI-CLAUDE",sessionId:"s1",body:"hello"});
 assert.ok(payload.recipientAiIds.includes("AI-OBSERVER"));
});
