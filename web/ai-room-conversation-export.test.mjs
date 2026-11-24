import test from "node:test";
import assert from "node:assert/strict";
import "../web/ai-room-conversation-export.js";
const exporter=globalThis.AIBridgeRoomConversationExport;
const messages=[
 {messageId:"m1",senderAiId:"AI-ALPHA",sequence:1,createdAtEpochMs:1764000000000,body:"First message\nwith line break"},
 {messageId:"m2",senderAiId:"AI-BRAVO",sequence:2,createdAtEpochMs:1764000005000,body:"Second message"}
];
test("TXT export preserves order, sender, timestamps and exact message body",()=>{
 const result=exporter.buildExport(messages,"room-42","txt","2026-11-24T12:00:00.000Z");
 assert.equal(result.messageCount,2);
 assert.match(result.filename,/room-42.*\.txt$/);
 assert.match(result.content,/AI-ALPHA/);
 assert.match(result.content,/First message\nwith line break/);
 assert.ok(result.content.indexOf("First message")<result.content.indexOf("Second message"));
 assert.match(result.mimeType,/text\/plain/);
});
test("JSON export is valid, structured and retains message text",()=>{
 const result=exporter.buildExport(messages,"room/42","json","2026-11-24T12:00:00.000Z");
 const parsed=JSON.parse(result.content);
 assert.equal(parsed.conversationId,"room/42");
 assert.equal(parsed.messageCount,2);
 assert.equal(parsed.messages[0].body,"First message\nwith line break");
 assert.match(result.filename,/room-42.*\.json$/);
 assert.match(result.mimeType,/application\/json/);
});
test("export filters malformed rows without mutating the source array",()=>{
 const source=[null,{body:"bad"},{senderAiId:"AI",body:"valid"}];
 const result=exporter.buildExport(source,"room","json","2026-11-24T12:00:00.000Z");
 assert.equal(result.messageCount,1);
 assert.equal(source.length,3);
});
test("export rejects invalid format, missing conversation and empty valid messages",()=>{
 assert.throws(()=>exporter.buildExport(messages,"room","csv"),/ROOM_EXPORT_FORMAT_INVALID/);
 assert.throws(()=>exporter.buildExport(messages,"","txt"),/ROOM_EXPORT_CONVERSATION_REQUIRED/);
 assert.throws(()=>exporter.buildExport([],"room","txt"),/ROOM_EXPORT_MESSAGES_EMPTY/);
 assert.throws(()=>exporter.buildExport(null,"room","txt"),/ROOM_EXPORT_MESSAGES_REQUIRED/);
});
test("download uses a local Blob URL and revokes it after clicking",()=>{
 const events=[];
 class FakeBlob{constructor(parts,options){this.parts=parts;this.options=options}}
 const anchor={click(){events.push("click")},remove(){events.push("remove")}};
 const env={Blob:FakeBlob,URL:{createObjectURL(blob){events.push(["create",blob.options.type]);return "blob:local"},revokeObjectURL(url){events.push(["revoke",url])}},document:{body:{append(){events.push("append")}},createElement(){return anchor}}};
 const result=exporter.download(messages,"room","txt",env);
 assert.equal(anchor.href,"blob:local");
 assert.equal(anchor.download,result.filename);
 assert.deepEqual(events.map(e=>Array.isArray(e)?e[0]:e),["create","append","click","remove","revoke"]);
});
test("room UI exposes local TXT and JSON export without unsafe HTML",async()=>{
 const {readFile}=await import("node:fs/promises");
 const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
 const server=await readFile(new URL("../server/http_server.py",import.meta.url),"utf8");
 assert.match(html,/id="exportConversationTxt"/);
 assert.match(html,/id="exportConversationJson"/);
 assert.match(html,/AIBridgeRoomConversationExport\.download/);
 assert.match(html,/ai-room-conversation-export\.js/);
 assert.doesNotMatch(html,/innerHTML/);
 assert.match(server,/ai-room-conversation-export\.js/);
});
