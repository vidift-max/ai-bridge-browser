import test from "node:test";
import assert from "node:assert/strict";
import "../web/ai-room-message-reply.js";
const reply=globalThis.AIBridgeRoomMessageReply;

test("reply draft quotes sender and preserves multiline message text",()=>{
 assert.equal(reply.buildReplyDraft({senderAiId:"AI-BRAVO",body:"linha 1\nlinha 2"}),"↪ Resposta a AI-BRAVO:\n> linha 1\n> linha 2\n\n");
});
test("reply draft safely falls back to a generic sender",()=>{
 assert.match(reply.buildReplyDraft({body:"conteúdo"}),/^↪ Resposta a IA:/);
});
test("reply draft rejects missing or blank message bodies",()=>{
 assert.throws(()=>reply.buildReplyDraft(null),/ROOM_REPLY_MESSAGE_REQUIRED/);
 assert.throws(()=>reply.buildReplyDraft({body:"  "}),/ROOM_REPLY_MESSAGE_REQUIRED/);
});
test("reply draft bounds quoted content to keep composer usable",()=>{
 const draft=reply.buildReplyDraft({senderAiId:"AI-X",body:"x".repeat(5000)});
 assert.ok(draft.length<4100);
 assert.ok(draft.includes("…"));
});
test("room UI exposes an accessible reply action and loads its served helper",async()=>{
 const {readFile}=await import("node:fs/promises");
 const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
 const server=await readFile(new URL("../server/http_server.py",import.meta.url),"utf8");
 assert.match(html,/ai-room-message-reply\.js/);
 assert.match(html,/AIBridgeRoomMessageReply\.buildReplyDraft/);
 assert.match(html,/Responder à mensagem/);
 assert.match(server,/ai-room-message-reply\.js/);
 assert.match(server,/def _room_message_reply_script/);
 assert.doesNotMatch(html,/innerHTML/);
});
