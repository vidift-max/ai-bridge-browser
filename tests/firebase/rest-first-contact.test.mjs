import { initializeTestEnvironment } from "@firebase/rules-unit-testing";
import { ref, set } from "firebase/database";
import fs from "node:fs";
import crypto from "node:crypto";

const PROJECT_ID = "demo-ai-bridge-rules";
const AUTH_ORIGIN = "http://127.0.0.1:9099";
const DATABASE_ORIGIN = "http://127.0.0.1:9000";
const DATABASE_NAMESPACE = PROJECT_ID;
const rules = fs.readFileSync(new URL("../../firebase/database.rules.json", import.meta.url), "utf8");
const env = await initializeTestEnvironment({
  projectId: PROJECT_ID,
  database: { host: "127.0.0.1", port: 9000, rules }
});

const checks = [];
function pass(name) {
  checks.push(name);
  console.log("PASS " + name);
}
function fail(message) {
  throw new Error(message);
}
async function signUp(label) {
  const response = await fetch(
    AUTH_ORIGIN + "/identitytoolkit.googleapis.com/v1/accounts:signUp?key=fake-api-key",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: label + "-" + crypto.randomUUID() + "@example.test", password: "test-only-password-123", returnSecureToken: true })
    }
  );
  const body = await response.json();
  if (!response.ok || typeof body.idToken !== "string" || typeof body.localId !== "string") {
    fail("Auth Emulator sign-up failed with HTTP " + response.status);
  }
  return { uid: body.localId, idToken: body.idToken };
}
function dbUrl(path, token, extra = {}) {
  const url = new URL(DATABASE_ORIGIN + path + ".json");
  url.searchParams.set("ns", DATABASE_NAMESPACE);
  if (token) url.searchParams.set("auth", token);
  for (const [key, value] of Object.entries(extra)) url.searchParams.set(key, value);
  return url.toString();
}
async function dbRequest(method, path, token, payload, expected = [200]) {
  const response = await fetch(dbUrl(path, token), {
    method,
    headers: payload === undefined ? {} : { "Content-Type": "application/json" },
    body: payload === undefined ? undefined : JSON.stringify(payload)
  });
  const bodyText = await response.text();
  let body = null;
  try { body = bodyText ? JSON.parse(bodyText) : null; } catch { fail("RTDB Emulator returned invalid JSON"); }
  if (!expected.includes(response.status)) {
    fail("RTDB Emulator " + method + " " + path + " returned unexpected HTTP " + response.status);
  }
  return { status: response.status, body };
}
const room = "/messenger/conversations/private-ai-01-ai-02";
let authUsers = [];
try {
  const [a, b, c] = await Promise.all([signUp("ai01"), signUp("ai02"), signUp("ai03")]);
  authUsers = [a, b, c];
  const fixture = {
    identities: {
      "AI-01": { aiId: "AI-01", uid: a.uid },
      "AI-02": { aiId: "AI-02", uid: b.uid },
      "AI-03": { aiId: "AI-03", uid: c.uid }
    },
    identitiesByUid: {
      [a.uid]: { aiId: "AI-01" },
      [b.uid]: { aiId: "AI-02" },
      [c.uid]: { aiId: "AI-03" }
    },
    conversations: {
      "private-ai-01-ai-02": {
        meta: { ownerAiId: "AI-01", kind: "GROUP", createdAtEpochMs: 1000 },
        members: { "AI-01": true, "AI-02": true, "AI-03": true },
        memberCount: 3,
        messages: {},
        acks: {}
      }
    }
  };
  await env.clearDatabase();
  await env.withSecurityRulesDisabled(async context => {
    await set(ref(context.database(), "/messenger"), fixture);
  });
  pass("fixture seeded through Emulator-only privileged test context");

  const identityA = await dbRequest("GET", "/messenger/identities/AI-01", a.idToken);
  const identityB = await dbRequest("GET", "/messenger/identities/AI-02", b.idToken);
  if (identityA.body?.uid !== a.uid || identityB.body?.uid !== b.uid) fail("Identity mapping did not match Auth Emulator UIDs");
  pass("Auth Emulator ID tokens resolve the correct AI identities");

  const roomRead = await dbRequest("GET", room, a.idToken);
  if (roomRead.body?.members?.["AI-01"] !== true || roomRead.body?.members?.["AI-02"] !== true) fail("Authorized sender could not read room membership");
  pass("AI-01 authenticated HTTP GET reads its conversation");

  await dbRequest("GET", room, c.idToken, undefined, [401, 403]);
  pass("non-member authenticated HTTP GET is denied");

  const nonce = "mission-81-" + crypto.randomUUID();
  const message = {
    senderAiId: "AI-01",
    recipientAiIds: { "AI-02": true },
    body: nonce,
    messageKind: "NORMAL",
    createdAtEpochMs: Date.now()
  };
  const posted = await dbRequest("POST", room + "/messages", a.idToken, message);
  const messageId = posted.body?.name;
  if (typeof messageId !== "string" || !messageId) fail("RTDB Emulator did not return a pushed message key");
  pass("AI-01 HTTP POST creates a recipient-bound message");

  let received = false;
  for (let attempt = 0; attempt < 8; attempt += 1) {
    const inbox = await dbRequest("GET", room + "/messages", b.idToken);
    const candidate = inbox.body?.[messageId];
    if (candidate?.body === nonce && candidate?.senderAiId === "AI-01" && candidate?.recipientAiIds?.["AI-02"] === true) {
      received = true;
      break;
    }
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  if (!received) fail("AI-02 did not receive the message through authenticated HTTP GET");
  pass("AI-02 authenticated HTTP GET receives AI-01 message");

  await dbRequest("PUT", room + "/acks/" + messageId + "/AI-02", b.idToken, true);
  const ack = await dbRequest("GET", room + "/acks/" + messageId + "/AI-02", a.idToken);
  if (ack.body !== true) fail("AI-01 could not verify AI-02 ACK");
  pass("AI-02 HTTP PUT ACK is verified by AI-01 HTTP GET");

  await dbRequest("PUT", room + "/acks/" + messageId + "/AI-03", c.idToken, true, [401, 403]);
  pass("room member not addressed by message cannot ACK over HTTP");

  const spoof = { ...message, recipientAiIds: { "AI-OUT": true }, body: "unauthorized-recipient" };
  await dbRequest("POST", room + "/messages", a.idToken, spoof, [401, 403]);
  pass("HTTP POST with non-member recipient is denied");

  console.log(JSON.stringify({
    state: "AUTHENTICATED_EMULATOR_HTTP_ROUND_TRIP_PASS",
    project: PROJECT_ID,
    identities: ["AI-01", "AI-02", "AI-03"],
    checks: checks.length,
    messageRoundTrip: "PASS",
    acknowledgement: "VERIFIED",
    externalFirebase: false,
    credentialsPrinted: false
  }));
} finally {
  await env.cleanup();
}
