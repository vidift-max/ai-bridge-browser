import test from "node:test";
import assert from "node:assert/strict";
import "../web/ai-room-inbox.js";
const inbox=globalThis.AIBridgeRoomInbox;
const rooms=[
 {conversationId:"team-alpha",kind:"GROUP",memberAiIds:["AI-ONE","AI-TWO"]},
 {conversationId:"private-beta",kind:"PRIVATE",memberAiIds:["AI-ONE","AI-THREE"]},
 {conversationId:"ops-room",kind:"GROUP",memberAiIds:["AI-ONE","AI-FOUR"]}
];
test("inbox search matches conversation id and member AI id case-insensitively",()=>{
 assert.deepEqual(inbox.filterRooms(rooms,"AI-three","ALL").map(x=>x.conversationId),["private-beta"]);
 assert.deepEqual(inbox.filterRooms(rooms,"TEAM","ALL").map(x=>x.conversationId),["team-alpha"]);
});
test("inbox kind filters private and group conversations",()=>{
 assert.deepEqual(inbox.filterRooms(rooms,"","PRIVATE").map(x=>x.conversationId),["private-beta"]);
 assert.deepEqual(inbox.filterRooms(rooms,"","GROUP").map(x=>x.conversationId),["team-alpha","ops-room"]);
});
test("search and kind filters compose without mutating source",()=>{
 const result=inbox.filterRooms(rooms,"AI-one","GROUP");
 assert.deepEqual(result.map(x=>x.conversationId),["team-alpha","ops-room"]);
 assert.equal(rooms.length,3);
});
test("page merge deduplicates overlapping records and retains cursor",()=>{
 const result=inbox.mergePage([rooms[0]],{conversations:[rooms[0],rooms[1]],nextCursor:"private-beta"});
 assert.deepEqual(result.rooms.map(x=>x.conversationId),["team-alpha","private-beta"]);
 assert.equal(result.nextCursor,"private-beta");
});
test("page merge rejects malformed pages and records",()=>{
 assert.throws(()=>inbox.mergePage([],{conversations:"bad"}),/invalid_conversation_page/);
 assert.throws(()=>inbox.mergePage([],{conversations:[{}]}),/invalid_conversation_record/);
 assert.throws(()=>inbox.mergePage([],{conversations:[],nextCursor:42}),/invalid_conversation_cursor/);
});
test("empty cursor marks the end of the inbox",()=>{
 assert.deepEqual(inbox.mergePage([],{conversations:[],nextCursor:null}),{rooms:[],nextCursor:null});
});
test("room page API uses bounded server cursor pagination and safe UI rendering",async()=>{
 const {readFile}=await import("node:fs/promises");
 const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
 const server=await readFile(new URL("../server/http_server.py",import.meta.url),"utf8");
 assert.match(html,/\/v1\/conversations\?limit=100&after=/);
 assert.match(html,/id="roomSearch"/);
 assert.match(html,/id="roomKindFilter"/);
 assert.match(html,/id="loadMoreRooms"/);
 assert.match(html,/AIBridgeRoomInbox\.filterRooms/);
 assert.match(html,/AIBridgeRoomInbox\.mergePage/);
 assert.match(server,/list_conversations\(self\._auth\(\), limit=limit, after=after\)/);
 assert.doesNotMatch(html,/innerHTML/);
});
