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
    "AI-OUT": { aiId: "AI-OUT", uid: "uid-out" },
    "AI-03": { aiId: "AI-03", uid: "uid-c" }
  },
  identitiesByUid: {
    "uid-a": { aiId: "AI-01" },
    "uid-b": { aiId: "AI-02" },
    "uid-out": { aiId: "AI-OUT" },
    "uid-c": { aiId: "AI-03" }
  },
  conversations: {
    "private-ai-01-ai-02": {
      meta: { ownerAiId: "AI-01", kind: "GROUP", createdAtEpochMs },
      members: { "AI-01": true, "AI-02": true, "AI-03": true },
      memberCount: 3,
      messages: { "existing-message": { senderAiId: "AI-01", recipientAiIds: { "AI-02": true }, body: "seeded-message", messageKind: "NORMAL", createdAtEpochMs: 1500 } }
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
const dbC = () => env.authenticatedContext("uid-c").database();
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
  await check("message recipient must be a room member", async () => {
    await assertFails(set(ref(dbA(), room + "/messages/nonmember-recipient"), { ...validMessage, recipientAiIds: { "AI-OUT": true } }));
  });
  await check("message must contain at least one recipient", async () => {
    await assertFails(set(ref(dbA(), room + "/messages/empty-recipient"), { ...validMessage, recipientAiIds: {} }));
  });
  await check("sender cannot spoof another AI identity", async () => {
    await assertFails(set(ref(dbA(), room + "/messages/message-2"), { ...validMessage, senderAiId: "AI-02" }));
  });
  await check("non-member cannot create a message", async () => {
    await assertFails(set(ref(dbOut(), room + "/messages/message-3"), { ...validMessage, senderAiId: "AI-OUT" }));
  });
  await check("recipient can write its own ACK", async () => {
    await assertSucceeds(set(ref(dbB(), room + "/acks/existing-message/AI-02"), true));
  });
  await check("sender cannot write ACK as recipient", async () => {
    await assertFails(set(ref(dbA(), room + "/acks/existing-message/AI-02"), true));
  });
  await check("room member who was not addressed cannot write ACK", async () => {
    await assertFails(set(ref(dbC(), room + "/acks/existing-message/AI-03"), true));
  });
  await check("recipient cannot ACK a nonexistent message", async () => {
    await assertFails(set(ref(dbB(), room + "/acks/missing-message/AI-02"), true));
  });
  await check("non-member cannot write ACK", async () => {
    await assertFails(set(ref(dbOut(), room + "/acks/existing-message/AI-OUT"), true));
  });
  await check("ACK must be boolean true", async () => {
    await assertFails(set(ref(dbB(), room + "/acks/existing-message/AI-02"), "yes"));
  });
  await check("AI-01 can create an owner-only group room for first-contact invitation", async () => {
    const roomPath = "/messenger/conversations/first-contact-room";
    await assertSucceeds(set(ref(dbA(), roomPath), {
      meta: { ownerAiId: "AI-01", kind: "GROUP", createdAtEpochMs: Date.now() },
      members: { "AI-01": true },
      memberCount: 1
    }));
  });
  await check("AI-01 can invite AI-02 and AI-02 can join the owner-only group", async () => {
    const roomPath = "/messenger/conversations/first-contact-room";
    const token = "FirstContactInviteToken_1234567890";
    const createdAtEpochMs = Date.now();
    const expiresAtEpochMs = createdAtEpochMs + 60000;
    await assertSucceeds(set(ref(dbA(), roomPath), {
      meta: { ownerAiId: "AI-01", kind: "GROUP", createdAtEpochMs },
      members: { "AI-01": true },
      memberCount: 1
    }));
    await assertSucceeds(set(ref(dbA(), "/messenger/invites/" + token), {
      conversationId: "first-contact-room",
      createdByAiId: "AI-01",
      expiresAtEpochMs
    }));
    await assertSucceeds(set(ref(dbB(), "/messenger/invitesByAi/AI-02/first-contact-room/" + token), true));
    await assertSucceeds(get(ref(dbB(), roomPath)));
    await assertSucceeds(set(ref(dbB(), roomPath), {
      meta: { ownerAiId: "AI-01", kind: "GROUP", createdAtEpochMs },
      members: { "AI-01": true, "AI-02": true },
      memberCount: 2
    }));
  });
  await check("AI-02 cannot create an invite for AI-01-owned group", async () => {
    const roomPath = "/messenger/conversations/first-contact-room";
    const token = "UnauthorizedInviteToken_1234567890";
    await env.withSecurityRulesDisabled(async context => {
      await set(ref(context.database(), roomPath), {
        meta: { ownerAiId: "AI-01", kind: "GROUP", createdAtEpochMs: 1000 },
        members: { "AI-01": true, "AI-02": true },
        memberCount: 2
      });
    });
    await assertFails(set(ref(dbB(), "/messenger/invites/" + token), {
      conversationId: "first-contact-room",
      createdByAiId: "AI-02",
      expiresAtEpochMs: Date.now() + 60000
    }));
  });
} finally {
  await env.cleanup();
}
if (failures > 0) process.exitCode = 1;
