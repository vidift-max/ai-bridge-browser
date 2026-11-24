import test from "node:test";
import assert from "node:assert/strict";
import "../web/ai-room-conversation-drafts.js";
const api=globalThis.AIBridgeConversationDrafts;
function memoryStorage(){const data=new Map();return {getItem:key=>data.has(key)?data.get(key):null,setItem:(key,value)=>data.set(key,value),removeItem:key=>data.delete(key),data};}

test("drafts persist independently for each conversation",()=>{
 const store=api.createDraftStore(memoryStorage());
 store.save("room-a","rascunho A");store.save("room-b","rascunho B");
 assert.equal(store.load("room-a"),"rascunho A");assert.equal(store.load("room-b"),"rascunho B");
});
test("empty drafts remove their stored entry",()=>{
 const storage=memoryStorage(),store=api.createDraftStore(storage);
 store.save("room-a","texto");assert.equal(store.save("room-a","  "),true);
 assert.equal(store.load("room-a"),"");assert.equal(storage.data.size,0);
});
test("draft length is bounded to the composer limit",()=>{
 const store=api.createDraftStore(memoryStorage()),value="x".repeat(6000);
 store.save("room-a",value);assert.equal(store.load("room-a").length,5000);
});
test("malformed stored data is ignored without breaking the composer",()=>{
 const storage=memoryStorage(),store=api.createDraftStore(storage);
 storage.setItem("aiBridgeDraft:room-a","{not-json");
 assert.equal(store.load("room-a"),"");
});
test("storage failures are reported and do not throw during typing",()=>{
 const storage={getItem(){throw Error("blocked")},setItem(){throw Error("quota")},removeItem(){throw Error("blocked")}};
 const store=api.createDraftStore(storage);
 assert.equal(store.load("room-a"),"");assert.equal(store.save("room-a","draft"),false);assert.equal(store.clear("room-a"),false);
});
test("invalid identifiers and non-string drafts are rejected",()=>{
 const store=api.createDraftStore(memoryStorage());
 assert.throws(()=>store.load(""),/DRAFT_CONVERSATION_REQUIRED/);
 assert.throws(()=>store.save("room-a",null),/DRAFT_TEXT_REQUIRED/);
});
test("room UI persists, restores, and clears drafts only after confirmed send",async()=>{
 const {readFile}=await import("node:fs/promises");
 const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
 const server=await readFile(new URL("../server/http_server.py",import.meta.url),"utf8");
 assert.match(html,/ai-room-conversation-drafts\.js/);
 assert.match(html,/conversationDraftStore\.save/);
 assert.match(html,/conversationDraftStore\.load/);
 assert.match(html,/conversationDraftStore\.clear/);
 assert.match(server,/ai-room-conversation-drafts\.js/);
 assert.doesNotMatch(html,/innerHTML/);
});
