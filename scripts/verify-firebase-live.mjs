import process from "node:process";

const hostingOrigins = [
  "https://ai-messenger-b97df.web.app",
  "https://ai-messenger-b97df.firebaseapp.com",
];
const databaseRoot = "https://ai-messenger-b97df-default-rtdb.firebaseio.com/.json";
const timeoutMs = 15_000;

async function request(url) {
  return fetch(url, {
    method: "GET",
    redirect: "manual",
    signal: AbortSignal.timeout(timeoutMs),
    headers: { accept: "text/html,application/json" },
  });
}

function fail(message) {
  console.error("FIREBASE_LIVE_SMOKE_FAILED: " + message);
  process.exitCode = 1;
}

async function verifyHosting(origin) {
  const inviteUrl = origin + "/i/smoke-conversation/abcdefghijklmnopqrst";
  let response;
  try {
    response = await request(inviteUrl);
  } catch (error) {
    fail(origin + " invite request failed: " + error.message);
    return;
  }
  if (response.status !== 200) {
    fail(origin + " invite route returned HTTP " + response.status);
    return;
  }
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.toLowerCase().includes("text/html")) {
    fail(origin + " invite route did not return HTML");
    return;
  }
  const body = await response.text();
  if (!body.includes("<h1>Convite AI Messenger</h1>")) {
    fail(origin + " invite route did not serve the expected invite page");
    return;
  }
  console.log("FIREBASE_HOSTING_INVITE_OK " + origin);
}

async function verifyDatabaseDenied() {
  let response;
  let body;
  try {
    response = await request(databaseRoot);
    body = await response.text();
  } catch (error) {
    fail("Realtime Database request failed: " + error.message);
    return;
  }
  if (response.status !== 401 && response.status !== 403) {
    fail("Unauthenticated Realtime Database root returned HTTP " + response.status + "; expected 401/403");
    return;
  }
  let payload;
  try {
    payload = JSON.parse(body);
  } catch {
    fail("Realtime Database denial response was not JSON");
    return;
  }
  if (typeof payload.error !== "string" || !/permission denied/i.test(payload.error)) {
    fail("Realtime Database did not explicitly report permission denied");
    return;
  }
  console.log("FIREBASE_DATABASE_PUBLIC_READ_BLOCKED");
}

async function main() {
  for (const origin of hostingOrigins) await verifyHosting(origin);
  if (process.exitCode !== 1) await verifyDatabaseDenied();
  if (process.exitCode !== 1) console.log("FIREBASE_LIVE_SMOKE_OK project=ai-messenger-b97df");
}

main().catch((error) => fail(error.message));
