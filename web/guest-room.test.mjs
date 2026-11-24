import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import guestRoom from "./guest-room.js";
const {buildGuestMessagePayload, requireSingleGuestRoom, createMessageDeduper, nextPollingDelayMs, validateGuestTransportContract, buildGuestLongPollPath, processGuestMessageBatch} = guestRoom;

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

test("message deduper suppresses repeated message identifiers and resets cleanly", () => {
  const deduper = createMessageDeduper();
  assert.equal(deduper.has("m1"),false);
  deduper.add("m1");
  assert.equal(deduper.has("m1"),true);
  deduper.add("m1");
  deduper.clear();
  assert.equal(deduper.has("m1"),false);
});

test("polling backoff is bounded and increases after failures", () => {
  assert.equal(nextPollingDelayMs(0),4000);
  assert.equal(nextPollingDelayMs(1),8000);
  assert.equal(nextPollingDelayMs(2),16000);
  assert.equal(nextPollingDelayMs(3),30000);
  assert.equal(nextPollingDelayMs(99),30000);
});

test("guest messenger renders untrusted content as text, not HTML", async () => {
  const source = await readFile(new URL("./guest-room.js", import.meta.url), "utf8");
  assert.match(source, /body\.textContent\s*=\s*message\.body/);
  assert.doesNotMatch(source, /\.innerHTML\s*=/);
});

test("guest messenger source contains bounded presence lifecycle", async () => {
  const source = await readFile(new URL("./guest-room.js", import.meta.url), "utf8");
  assert.match(source, /\/v1\/presence\/heartbeat/);
  assert.match(source, /\/v1\/presence\/leave/);
  assert.match(source, /visibilityState/);
  assert.match(source, /presenceTimer/);
});

test("guest messenger source contains reliability safeguards", async () => {
  const source = await readFile(new URL("./guest-room.js", import.meta.url), "utf8");
  assert.match(source, /createMessageDeduper/);
  assert.match(source, /nextPollingDelayMs/);
  assert.match(source, /MAX_POLL_DELAY_MS/);
  assert.match(source, /\/messages\/wait\?/);
  assert.match(source, /after: String\(afterSequence\)/);
  assert.match(source, /timeout: String\(transport\.defaultWaitSeconds\)/);
  assert.match(source, /clearTimeout\(timer\)/);
  assert.match(source, /schedulePolling\(0\)/);
});

test("guest messenger aborts stale long-poll requests during session teardown", async () => {
  const source = await readFile(new URL("./guest-room.js", import.meta.url), "utf8");
  assert.match(source, /AbortController/);
  assert.match(source, /activePollController/);
  assert.match(source, /error\.name === "AbortError"/);
  assert.match(source, /sessionGeneration/);
  assert.match(source, /abortActivePoll\(\)/);
});

test("guest messenger aborts an in-flight long poll when the document becomes hidden", async () => {
  const source = await readFile(new URL("./guest-room.js", import.meta.url), "utf8");
  assert.match(source, /doc\.visibilityState === "visible"/);
  assert.match(source, /else \{\s*if \(timer !== null\) clearTimeout\(timer\);\s*timer = null;\s*abortActivePoll\(\);/);
});

test("guest messenger ignores late responses from an older session generation", async () => {
  const source = await readFile(new URL("./guest-room.js", import.meta.url), "utf8");
  assert.match(source, /if \(generation !== sessionGeneration \|\| !sessionToken \|\| !room\) return;/);
});


test("guest messenger negotiates and validates the authorized transport contract before opening the room", async () => {
  const source = await readFile(new URL("./guest-room.js", import.meta.url), "utf8");
  assert.match(source, /\/v1\/conversations\/.*\/transport/);
  assert.match(source, /validateGuestTransportContract\(transport, room\.conversationId\)/);
  assert.match(source, /payload\.authorized !== true/);
  assert.match(source, /payload\.defaultTransport !== "HTTP_LONG_POLL"/);
  assert.match(source, /guest_transport_unavailable/);
});

function validTransportContract(overrides = {}) {
  return {
    contractVersion: 1,
    conversationId: "room-a",
    authorized: true,
    defaultTransport: "HTTP_LONG_POLL",
    transports: {
      httpLongPoll: {enabled: true, minWaitSeconds: 0, maxWaitSeconds: 25,
        defaultWaitSeconds: 20, maxBatchSize: 100},
      webSocket: {enabled: false},
      serverPush: {enabled: false}
    },
    cursor: {type: "sequence", ackRequired: true},
    ...overrides
  };
}

test("transport validator accepts the versioned bounded long-poll contract", () => {
  assert.deepEqual(validateGuestTransportContract(validTransportContract(), "room-a"), {
    minWaitSeconds: 0, maxWaitSeconds: 25, defaultWaitSeconds: 20, maxBatchSize: 100
  });
});


test("transport validator rejects wrong room, version, authorization, and transport", () => {
  const cases = [
    [validTransportContract({conversationId: "room-b"}), "room-a"],
    [validTransportContract({contractVersion: 2}), "room-a"],
    [validTransportContract({authorized: false}), "room-a"],
    [validTransportContract({defaultTransport: "WEBSOCKET"}), "room-a"]
  ];
  for (const [contract, roomId] of cases) {
    assert.throws(() => validateGuestTransportContract(contract, roomId), /guest_transport_unavailable/);
  }
});

test("transport validator rejects unsafe bounds, cursor changes, and unimplemented transports", () => {
  const mutations = [
    value => { value.transports.httpLongPoll.maxWaitSeconds = 26; },
    value => { value.transports.httpLongPoll.defaultWaitSeconds = 30; },
    value => { value.transports.httpLongPoll.maxBatchSize = 101; },
    value => { value.transports.httpLongPoll.minWaitSeconds = -1; },
    value => { value.cursor.ackRequired = false; },
    value => { value.cursor.type = "opaque"; },
    value => { value.transports.webSocket.enabled = true; },
    value => { value.transports.serverPush.enabled = true; }
  ];
  for (const mutate of mutations) {
    const contract = structuredClone(validTransportContract());
    mutate(contract);
    assert.throws(() => validateGuestTransportContract(contract, "room-a"), /guest_transport_unavailable/);
  }
});


test("guest room entry uses strict transport validation for the exact room", async () => {
  const source = await readFile(new URL("./guest-room.js", import.meta.url), "utf8");
  assert.match(source, /validateGuestTransportContract\(transport, room\.conversationId\)/);
  assert.match(source, /payload\.contractVersion !== 1/);
  assert.match(source, /payload\.conversationId !== conversationId/);
  assert.match(source, /poll\.maxWaitSeconds > 25/);
  assert.match(source, /poll\.maxBatchSize > 100/);
  assert.match(source, /cursor\.ackRequired !== true/);
});

test("long-poll request uses negotiated timeout and batch size", () => {
  const transport = validateGuestTransportContract(validTransportContract(), "room-a");
  assert.equal(buildGuestLongPollPath("room-a", 17, transport),
    "/v1/conversations/room-a/messages/wait?after=17&limit=100&timeout=20");
});


test("long-poll request honors a server-advertised narrower profile and encodes room IDs", () => {
  const transport = {minWaitSeconds: 0, maxWaitSeconds: 12, defaultWaitSeconds: 7, maxBatchSize: 25};
  assert.equal(buildGuestLongPollPath("room/a b", 0, transport),
    "/v1/conversations/room%2Fa%20b/messages/wait?after=0&limit=25&timeout=7");
});

test("long-poll request builder rejects invalid cursor and out-of-contract limits", () => {
  const valid = {minWaitSeconds: 0, maxWaitSeconds: 25, defaultWaitSeconds: 20, maxBatchSize: 100};
  for (const [room, cursor, config] of [
    ["room-a", -1, valid],
    ["room-a", 1.5, valid],
    ["room-a", Number.MAX_SAFE_INTEGER + 1, valid],
    ["room-a", 0, {...valid, defaultWaitSeconds: 26}],
    ["room-a", 0, {...valid, maxWaitSeconds: 26}],
    ["room-a", 0, {...valid, maxBatchSize: 101}],
    ["", 0, valid]
  ]) {
    assert.throws(() => buildGuestLongPollPath(room, cursor, config), /guest_transport_unavailable/);
  }
});


test("guest polling consumes negotiated configuration and clears it on session teardown", async () => {
  const source = await readFile(new URL("./guest-room.js", import.meta.url), "utf8");
  assert.match(source, /transportConfig = validateGuestTransportContract\(transport, room\.conversationId\)/);
  assert.match(source, /buildGuestLongPollPath\(room\.conversationId, sequence, transportConfig\)/);
  assert.match(source, /transportConfig = null/);
  assert.doesNotMatch(source, /messages\/wait\?after=" \+ sequence \+ "&limit=100&timeout=20/);
});


test("message batch advances cursor only after each acknowledgement succeeds", async () => {
  const rendered = [];
  const acknowledged = [];
  let sequence = 0;
  await assert.rejects(async () => {
    sequence = await processGuestMessageBatch([
      {messageId:"m1",sequence:1},
      {messageId:"m2",sequence:2}
    ], sequence, message => rendered.push(message.messageId), async message => {
      acknowledged.push(message.messageId);
      if (message.messageId === "m2") throw new Error("ack_unavailable");
    });
  }, /ack_unavailable/);
  assert.deepEqual(rendered, ["m1","m2"]);
  assert.deepEqual(acknowledged, ["m1","m2"]);
  assert.equal(sequence, 0);
});

test("duplicate rendered messages are still acknowledged before cursor advances", async () => {
  const rendered = [];
  const acknowledged = [];
  const sequence = await processGuestMessageBatch(
    [{messageId:"m1",sequence:1},{messageId:"m2",sequence:2}],
    0,
    message => { if (!rendered.includes(message.messageId)) rendered.push(message.messageId); },
    async message => acknowledged.push(message.messageId)
  );
  assert.deepEqual(rendered, ["m1","m2"]);
  assert.deepEqual(acknowledged, ["m1","m2"]);
  assert.equal(sequence, 2);
});

test("stale session stops cursor advancement after acknowledgement", async () => {
  let current = true;
  const sequence = await processGuestMessageBatch(
    [{messageId:"m1",sequence:1},{messageId:"m2",sequence:2}],
    0, () => {}, async () => { current = false; }, () => current
  );
  assert.equal(sequence, 0);
});

test("message batch rejects unsafe sequence values without committing cursor", async () => {
  await assert.rejects(
    processGuestMessageBatch([{messageId:"m1",sequence:Number.MAX_SAFE_INTEGER + 1}],
      0, () => {}, async () => {}),
    /invalid_message_sequence/
  );
});
