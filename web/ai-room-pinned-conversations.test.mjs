import test from "node:test";
import assert from "node:assert/strict";
import "../web/ai-room-pinned-conversations.js";
const api=globalThis.AIBridgePinnedConversations;
function storage(seed={}){const data=new Map(Object.entries(seed));return {getItem:key=>data.has(key)?data.get(key):null,setItem:(key,value)=>data.set(key,value)}}
const rooms=[{conversationId:"room-a"},{conversationId:"room-b"},{conversationId:"room-c"}];
test("pin and unpin are persisted per conversation",()=>{const s=api.createStore(storage());assert.equal(s.toggle("room-b"),true);assert.equal(s.has("room-b"),true);assert.deepEqual(s.list(),["room-b"]);assert.equal(s.toggle("room-b"),false);assert.equal(s.has("room-b"),false)});
test("pinned conversations sort first and preserve relative order",()=>{const s=api.createStore(storage());s.toggle("room-c");s.toggle("room-a");assert.deepEqual(s.sort(rooms).map(x=>x.conversationId),["room-a","room-c","room-b"])});
test("malformed and duplicate stored ids are sanitized",()=>{const s=api.createStore(storage({[api.KEY]:'["room-a",null,"room-a",4,""]'}));assert.deepEqual(s.list(),["room-a"])});
test("malformed JSON and non-array values safely produce an empty list",()=>{for(const value of ["{bad","null",'{"id":"room-a"}']){const s=api.createStore(storage({[api.KEY]:value}));assert.deepEqual(s.list(),[])}});
test("invalid ids and invalid room collections are rejected",()=>{const s=api.createStore(storage());assert.throws(()=>s.toggle(""),/invalid_conversation_id/);assert.throws(()=>s.sort(null),/invalid_conversation_list/)});
test("unknown pinned ids do not affect current inbox records",()=>{const s=api.createStore(storage());s.toggle("removed-room");assert.deepEqual(s.sort(rooms),rooms)});
test("storage read and write failures are surfaced to caller",()=>{const broken={getItem(){throw Error("blocked")},setItem(){throw Error("blocked")}};const s=api.createStore(broken);assert.throws(()=>s.list(),/blocked/);assert.throws(()=>s.toggle("room-a"),/blocked/)});
