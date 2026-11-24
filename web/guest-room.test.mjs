import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import guestRoom from "./guest-room.js";
const {buildGuestMessagePayload, requireSingleGuestRoom} = guestRoom;

test("guest room contract accepts exactly one room", () => {
  const room = requireSingleGuestRoom({conversations:[{
    conversationId:"room-a", memberAiIds:["AI-ADMIN","AI-GUEST-1"]
  }]});
  assert.equal(room.conversationId,"room-a");
  assert.deepEqual(room.memberAiIds,["AI-ADMIN","AI-GUEST-1"]);
});
test("guest room contract fails closed for zero or multiple rooms", () => {
  assert.throws(()=>requireSingleGuestRoom({conversations:[]}),/guest_room_scope_invalid/);
  assert.throws(()=>requireSingleGuestRoom({conversations:[
    {conversationId:"a",memberAiIds:["x","y"]},
    {conversationId:"b",memberAiIds:["x","z"]}
  ]}),/guest_room_scope_invalid/);
});
test("guest room contract rejects malformed or undersized memberships", () => {
  assert.throws(()=>requireSingleGuestRoom({conversations:[{conversationId:"a",memberAiIds:["only"]}]}),
    /guest_room_scope_invalid/);
});
test("message payload sends only to other members of the authorized room", () => {
  const room={conversationId:"room-a",memberAiIds:["AI-ADMIN","AI-GUEST-1","AI-OTHER"]};
  const payload=buildGuestMessagePayload(room,"AI-GUEST-1"," hello ",{
    messageId:"message-1",clientRequestId:"request-1"
  });
  assert.deepEqual(payload.recipientAiIds,["AI-ADMIN","AI-OTHER"]);
  assert.equal(payload.body,"hello");
  assert.equal(payload.conversationId,"room-a");
});
test("message payload rejects non-member sender and invalid body", () => {
  const room={conversationId:"room-a",memberAiIds:["AI-ADMIN","AI-GUEST-1"]};
  assert.throws(()=>buildGuestMessagePayload(room,"AI-OUTSIDER","hello"),/guest_room_scope_invalid/);
  assert.throws(()=>buildGuestMessagePayload(room,"AI-GUEST-1","  "),/invalid_message/);
  assert.throws(()=>buildGuestMessagePayload(room,"AI-GUEST-1","x".repeat(5001)),/invalid_message/);
});

test("guest messenger renders untrusted content as text, not HTML", async () => {
  const source = await readFile(new URL("./guest-room.js", import.meta.url), "utf8");
  assert.match(source, /body\.textContent\s*=\s*message\.body/);
  assert.doesNotMatch(source, /\.innerHTML\s*=/);
});
