import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import {readFile} from "node:fs/promises";

const source=await readFile(new URL("./ai-conversation-host-client.js",import.meta.url),"utf8");
function fixture({privateRoom=true,wrongRecipient=false}={}){
 const calls=[];
 const context={room:{conversationId:"private-ab",kind:privateRoom?"PRIVATE":"GROUP",memberAiIds:["AI-A","AI-B"]},identity:{aiId:"AI-A"}};
 const scope={window:{crypto:{randomUUID:()=>"request-uuid"}}};
 vm.runInNewContext(source,scope);
 const client=scope.window.AIBridgeAgentHostClient.create({
  getContext:()=>context,
  api:async(path,options)=>{calls.push({path,options});if(path.endsWith("/session/register"))return {session:{conversationId:"private-ab",aiId:"AI-A",ttlSeconds:1800}};if(path.endsWith("/conversation/turn"))return {message:{conversationId:"private-ab",senderAiId:"AI-B",recipientAiIds:wrongRecipient?["AI-C"]:["AI-A"],body:"Resposta de B"},attestation:{signature:"signed"}};if(path.endsWith("/attestation/verify"))return {valid:true};throw new Error("unexpected_path");}
 });
 return {client,calls,scope,context};
}
test("host client registers only the current authenticated identity for the selected room",async()=>{
 const f=fixture();const result=await f.client.registerSession();
 assert.equal(result.aiId,"AI-A");
 assert.equal(f.calls[0].path,"/v1/ai/conversation/session/register");
 assert.deepEqual(JSON.parse(f.calls[0].options.body),{conversationId:"private-ab"});
});
test("host client requests a specific room member and returns the attestation envelope",async()=>{
 const f=fixture();const result=await f.client.requestAgent({conversationId:"private-ab",agentId:"AI-B",prompt:"Olá"});
 assert.equal(result.agentId,"AI-B");assert.equal(result.body,"Resposta de B");
 assert.equal(JSON.parse(result.attestation).signature,"signed");
 assert.deepEqual(JSON.parse(f.calls[0].options.body),{
  conversationId:"private-ab",agentId:"AI-B",requestId:"browser-request-uuid",prompt:"Olá"
 });
});
test("host client verifies attestations through the server without exposing its key",async()=>{
 const f=fixture();const result={body:"Resposta",attestation:JSON.stringify({signature:"signed"})};
 assert.equal(await f.client.verifyAttestation(result),true);
 assert.equal(f.calls[0].path,"/v1/ai/provider/attestation/verify");
 assert.equal(JSON.parse(f.calls[0].options.body).responseText,"Resposta");
 assert.equal(JSON.parse(f.calls[0].options.body).agentId,"AI-B");
});
test("host client refuses group rooms and identities outside the room",async()=>{
 const f=fixture({privateRoom:false});
 await assert.rejects(f.client.registerSession(),/AI_CONVERSATION_HOST_PRIVATE_ROOM_REQUIRED/);
 await assert.rejects(f.client.requestAgent({conversationId:"private-ab",agentId:"AI-OUTSIDER",prompt:"x"}),/AI_CONVERSATION_HOST_PRIVATE_ROOM_REQUIRED/);
 assert.equal(f.calls.length,0);
});
test("host client rejects responses addressed to a different identity",async()=>{
 const f=fixture({wrongRecipient:true});
 await assert.rejects(f.client.requestAgent({conversationId:"private-ab",agentId:"AI-B",prompt:"Olá"}),/AI_CONVERSATION_HOST_RESPONSE_INVALID/);
});
