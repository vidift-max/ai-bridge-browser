import fs from "node:fs";
import { initializeTestEnvironment, assertFails, assertSucceeds } from "@firebase/rules-unit-testing";
import { ref, get, set } from "firebase/database";

const projectId = "demo-ai-bridge-rules";
const rules = fs.readFileSync(new URL("../../firebase/database.rules.json", import.meta.url), "utf8");
const env = await initializeTestEnvironment({ projectId, database: { rules } });

const fixture = {
  identities: {
    "AI-01": { aiId: "AI-01", uid: "uid-a" },
    "AI-02": { aiId: "AI-02", uid: "uid-b" },
    "AI-OUT": { aiId: "AI-OUT", uid: "uid-out" }
  },
  identitiesByUid: {
    "uid-a": { aiId: "AI-01" },
    "uid-b": { aiId: "AI-02" },
    "uid-out": { aiId: "AI-OUT" }
  },
  conversations: {
    "private-ai-01-ai-02": {
      meta: { ownerAiId: "AI-01", kind: "PRIVATE", createdAtEpochMs: 1000 },
      members: { "AI-01": true, "AI-02": true },
      memberCount: 2,
      messages: {}
    }
  }
};

async function seed() {
  await env.clearDatabase();
  await env.withSecurityRulesDisabled(async context => {
    await set(ref(context.database(), "/messenger"), fixture);
  });
}

const dbA = () => env.authenticatedContext("uid-a").database();
const dbB = () => env.authenticatedContext("uid-b").database();
const dbOut = () => env.authenticatedContext("uid-out").database();
const room = "/messenger/conversations/private-ai-01-ai-02";
const validMessage = {
  senderAiId: "AI-01",
  recipientAiIds: { "AI-02": true },
  body: "first-contact-emulator-test",
  messageKind: "NORMAL",
  createdAtEpochMs: 2000
};

let failures = 0;
async function check(name, fn) {
  try {
    await seed();
    await fn();
    console.log("PASS " + name);
  } catch (error) {
    failures += 1;
    console.error("FAIL " + name + ": " + (error?.message || String(error)));
  }
}

try {
  await check("AI-01 member can read the messages collection", async () => {
    await assertSucceeds(get(ref(dbA(), room + "/messages")));
  });
  await check("AI-02 member can read the messages collection", async () => {
    await assertSucceeds(get(ref(dbB(), room + "/messages")));
  });
  await check("non-member cannot read the messages collection", async () => {
    await assertFails(get(ref(dbOut(), room + "/messages")));
  });
  await check("authorized sender can create a message", async () => {
    await assertSucceeds(set(ref(dbA(), room + "/messages/message-1"), validMessage));
  });
  await check("sender cannot spoof another AI identity", async () => {
    await assertFails(set(ref(dbA(), room + "/messages/message-2"), { ...validMessage, senderAiId: "AI-02" }));
  });
  await check("non-member cannot create a message", async () => {
    await assertFails(set(ref(dbOut(), room + "/messages/message-3"), { ...validMessage, senderAiId: "AI-OUT" }));
  });
  await check("recipient can write its own ACK", async () => {
    await assertSucceeds(set(ref(dbB(), room + "/acks/message-1/AI-02"), true));
  });
  await check("sender cannot write ACK as recipient", async () => {
    await assertFails(set(ref(dbA(), room + "/acks/message-1/AI-02"), true));
  });
  await check("non-member cannot write ACK", async () => {
    await assertFails(set(ref(dbOut(), room + "/acks/message-1/AI-OUT"), true));
  });
  await check("ACK must be boolean true", async () => {
    await assertFails(set(ref(dbB(), room + "/acks/message-1/AI-02"), "yes"));
  });
} finally {
  await env.cleanup();
}
if (failures > 0) process.exitCode = 1;
