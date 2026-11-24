import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import vm from "node:vm";
const source=await readFile(new URL("./ai-room-admission.js",import.meta.url),"utf8");
function fixture(options={}){
 const sessions=new Map();
 const registry={getSession:id=>sessions.get(id)||null};
 const context={window:{},URL};vm.runInNewContext(source,context);
 let time=1000;
 const rooms=context.window.AIBridgeRoomAdmission.create({sessions:registry,now:()=>time,maxParticipants:options.max||3});
 function addSession(id,provider="provider"){sessions.set(id,{sessionId:id,providerId:provider,state:"CONNECTED"});}
 addSession("s-coord","openai");addSession("s-two","anthropic");addSession("s-three","google");
 const room=rooms.createRoom({roomId:"room-main",coordinatorAiId:"AI-GPT-6",coordinatorSessionId:"s-coord"});
 function invite(aiId,role="PARTICIPANT",id="inv-"+aiId,expiresAt=time+5000){
  return rooms.issueInvitation({roomId:"room-main",invitationId:id,aiId,role,expiresAt,issuedByAiId:"AI-GPT-6"});
 }
 return {rooms,addSession,invite,room,advance(ms){time+=ms;},sessions};
}
test("room starts with one connected coordinator identity",()=>{
 const f=fixture();assert.equal(f.room.participants.length,1);
 assert.equal(f.room.participants[0].aiId,"AI-GPT-6");
 assert.equal(f.room.participants[0].role,"COORDINATOR");
});
test("room admission requires a connected session and coordinator-issued invitation",()=>{
 const f=fixture();f.invite("AI-CLAUDE");f.addSession("s-offline");
 f.sessions.set("s-offline",{sessionId:"s-offline",providerId:"x",state:"OFFLINE"});
 assert.throws(()=>f.rooms.admit({roomId:"room-main",invitationId:"inv-AI-CLAUDE",aiId:"AI-CLAUDE",sessionId:"s-offline"}),/CONNECTED_SESSION_REQUIRED/);
 assert.throws(()=>f.rooms.issueInvitation({roomId:"room-main",invitationId:"x",aiId:"AI-X",role:"PARTICIPANT",expiresAt:5000,issuedByAiId:"AI-CLAUDE"}),/COORDINATOR_REQUIRED/);
});
test("one-time invitation binds exact AI identity and is consumed on admission",()=>{
 const f=fixture();f.invite("AI-CLAUDE");
 assert.throws(()=>f.rooms.admit({roomId:"room-main",invitationId:"inv-AI-CLAUDE",aiId:"AI-GEMINI",sessionId:"s-two"}),/INVITATION_IDENTITY_MISMATCH/);
 f.rooms.admit({roomId:"room-main",invitationId:"inv-AI-CLAUDE",aiId:"AI-CLAUDE",sessionId:"s-two"});
 assert.throws(()=>f.rooms.admit({roomId:"room-main",invitationId:"inv-AI-CLAUDE",aiId:"AI-CLAUDE",sessionId:"s-two"}),/INVITATION_NOT_AVAILABLE/);
});
test("invitation expiry is bounded and exact-boundary expiry fails closed",()=>{
 const f=fixture();assert.throws(()=>f.invite("AI-X","PARTICIPANT","bad",f.rooms.getRoom("room-main").createdAt),/INVITATION_EXPIRY_INVALID/);
 f.invite("AI-CLAUDE");f.advance(5000);
 assert.throws(()=>f.rooms.admit({roomId:"room-main",invitationId:"inv-AI-CLAUDE",aiId:"AI-CLAUDE",sessionId:"s-two"}),/INVITATION_EXPIRED/);
});
test("room capacity and duplicate sessions are enforced",()=>{
 const f=fixture({max:2});f.invite("AI-CLAUDE");f.rooms.admit({roomId:"room-main",invitationId:"inv-AI-CLAUDE",aiId:"AI-CLAUDE",sessionId:"s-two"});
 f.invite("AI-GEMINI");assert.throws(()=>f.rooms.admit({roomId:"room-main",invitationId:"inv-AI-GEMINI",aiId:"AI-GEMINI",sessionId:"s-three"}),/ROOM_CAPACITY_REACHED/);
});
test("observers can be admitted but cannot send room messages",()=>{
 const f=fixture();f.invite("AI-OBSERVER","OBSERVER");f.rooms.admit({roomId:"room-main",invitationId:"inv-AI-OBSERVER",aiId:"AI-OBSERVER",sessionId:"s-two"});
 assert.throws(()=>f.rooms.authorizeMessage({roomId:"room-main",aiId:"AI-OBSERVER",sessionId:"s-two"}),/ROOM_ROLE_READ_ONLY/);
});
test("participant message authorization is bound to room identity and session",()=>{
 const f=fixture();f.invite("AI-CLAUDE");f.rooms.admit({roomId:"room-main",invitationId:"inv-AI-CLAUDE",aiId:"AI-CLAUDE",sessionId:"s-two"});
 assert.equal(f.rooms.authorizeMessage({roomId:"room-main",aiId:"AI-CLAUDE",sessionId:"s-two"}).authorized,true);
 assert.throws(()=>f.rooms.authorizeMessage({roomId:"room-main",aiId:"AI-CLAUDE",sessionId:"s-three"}),/ROOM_MEMBERSHIP_REQUIRED/);
});
test("coordinator can revoke one member without disturbing other participants",()=>{
 const f=fixture();f.invite("AI-CLAUDE");f.rooms.admit({roomId:"room-main",invitationId:"inv-AI-CLAUDE",aiId:"AI-CLAUDE",sessionId:"s-two"});
 f.invite("AI-GEMINI");f.rooms.admit({roomId:"room-main",invitationId:"inv-AI-GEMINI",aiId:"AI-GEMINI",sessionId:"s-three"});
 f.rooms.revoke({roomId:"room-main",byAiId:"AI-GPT-6",aiId:"AI-CLAUDE"});
 assert.throws(()=>f.rooms.authorizeMessage({roomId:"room-main",aiId:"AI-CLAUDE",sessionId:"s-two"}),/ROOM_MEMBERSHIP_REQUIRED/);
 assert.equal(f.rooms.authorizeMessage({roomId:"room-main",aiId:"AI-GEMINI",sessionId:"s-three"}).authorized,true);
});
test("participants can leave while coordinator cannot leave without closing room",()=>{
 const f=fixture();f.invite("AI-CLAUDE");f.rooms.admit({roomId:"room-main",invitationId:"inv-AI-CLAUDE",aiId:"AI-CLAUDE",sessionId:"s-two"});
 assert.equal(f.rooms.leave({roomId:"room-main",aiId:"AI-CLAUDE",sessionId:"s-two"}).status,"LEFT");
 assert.throws(()=>f.rooms.leave({roomId:"room-main",aiId:"AI-GPT-6",sessionId:"s-coord"}),/COORDINATOR_MUST_CLOSE_ROOM/);
});
test("closed rooms revoke pending invitations and reject further operations",()=>{
 const f=fixture();f.invite("AI-CLAUDE");
 const closed=f.rooms.closeRoom({roomId:"room-main",byAiId:"AI-GPT-6"});
 assert.equal(closed.status,"CLOSED");
 assert.equal(closed.participants[0].status,"ROOM_CLOSED");
 assert.throws(()=>f.rooms.issueInvitation({roomId:"room-main",invitationId:"later",aiId:"AI-X",role:"PARTICIPANT",expiresAt:5000,issuedByAiId:"AI-GPT-6"}),/ROOM_NOT_ACTIVE/);
});
test("public snapshots never expose invitations or session credentials",()=>{
 const f=fixture();f.invite("AI-CLAUDE");
 const snapshot=f.rooms.getRoom("room-main");
 assert.equal("invitations" in snapshot,false);
 assert.equal("token" in snapshot.participants[0],false);
 assert.equal(Object.isFrozen(snapshot),true);
});
test("source documents room-scoped identity and separation of membership from tools",async()=>{
 const doc=await readFile(new URL("../docs/MISSION_51_MULTI_AI_ROOM_ADMISSION.md",import.meta.url),"utf8");
 assert.match(doc,/Room membership does not grant tool permissions/);
 assert.match(doc,/HTTP Long Poll/);
});
