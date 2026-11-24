import test from "node:test";
import assert from "node:assert/strict";
import "../web/ai-room-message-search.js";
const search=globalThis.AIBridgeRoomMessageSearch;
const messages=[
 {messageId:"m1",senderAiId:"AI-ALPHA",body:"The browser is ready"},
 {messageId:"m2",senderAiId:"AI-BRAVO",body:"Backend validation passed"},
 {messageId:"m3",senderAiId:"AI-ALPHA",body:"Android regression is running"}
];
test("message search matches body case-insensitively",()=>{
 assert.deepEqual(search.filterMessages(messages,"BROWSER").map(x=>x.messageId),["m1"]);
});
test("message search also matches sender identity",()=>{
 assert.deepEqual(search.filterMessages(messages,"bravo").map(x=>x.messageId),["m2"]);
});
test("sender filter composes with body search",()=>{
 assert.deepEqual(search.filterMessages(messages,"regression","AI-ALPHA").map(x=>x.messageId),["m3"]);
});
test("empty search returns all valid messages without mutating source",()=>{
 assert.deepEqual(search.filterMessages(messages,"").map(x=>x.messageId),["m1","m2","m3"]);
 assert.equal(messages.length,3);
});
test("invalid message collection is rejected and malformed rows are ignored",()=>{
 assert.throws(()=>search.filterMessages(null,""),/ROOM_MESSAGES_REQUIRED/);
 assert.deepEqual(search.filterMessages([null,{},...messages],"ready").map(x=>x.messageId),["m1"]);
});
test("message search trims query and sender filters",()=>{
 assert.deepEqual(search.filterMessages(messages,"  READY  "," AI-ALPHA ").map(x=>x.messageId),["m1"]);
});
test("room UI wires a local loaded-message search without unsafe HTML",async()=>{
 const {readFile}=await import("node:fs/promises");
 const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
 const server=await readFile(new URL("../server/http_server.py",import.meta.url),"utf8");
 assert.match(html,/id="messageSearch"/);
 assert.match(html,/id="messageSearchCount"/);
 assert.match(html,/AIBridgeRoomMessageSearch\.filterMessages/);
 assert.match(html,/ai-room-message-search\.js/);
 assert.doesNotMatch(html,/innerHTML/);
 assert.match(server,/ai-room-message-search\.js/);
});
