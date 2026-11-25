import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const rooms = await readFile(new URL("./rooms.html", import.meta.url), "utf8");
const adapter = await readFile(new URL("./ai-room-ui-messenger.js", import.meta.url), "utf8");
const invite = await readFile(new URL("./invite.html", import.meta.url), "utf8");
const native = await readFile(new URL("../app/src/main/java/com/vidiftmax/aibridgebrowser/MessengerInviteActivity.java", import.meta.url), "utf8");
const manifest = await readFile(new URL("../app/src/main/AndroidManifest.xml", import.meta.url), "utf8");

test("one selected room owns the shared participants and message timeline", () => {
  assert.match(rooms, /id="conversation"/);
  assert.match(rooms, /id="participants"/);
  assert.match(rooms, /id="messages"/);
  assert.match(rooms, /activeRoom=room/);
  assert.match(rooms, /ensureRoomMessenger\(\)\.load\(\)/);
  assert.match(adapter, /current\.room\.conversationId/);
  assert.match(adapter, /current\.room\.memberAiIds\.filter\(id=>id!==current\.identity\.aiId\)/);
});

test("one group conversation supports multiple selected AI participants", () => {
  assert.match(rooms, /option value="GROUP">Grupo · até 19 participantes/);
  assert.match(rooms, /id="conversationPeers" multiple/);
  assert.match(rooms, /Selecione uma IA além da sua identidade/);
});

test("group invite is scoped to the selected conversation", () => {
  assert.match(rooms, /function createInvite\(room\)\{inviteRoom=room/);
  assert.match(rooms, /\/v1\/conversations\/'.*\/invites/);
  assert.match(rooms, /inviteRoom\.conversationId/);
});

test("invite secrets are placed in a URL fragment and removed from browser history", () => {
  assert.match(rooms, /\/invite#'.*invite\.invite_id/);
  assert.match(invite, /location\.hash\.slice\(1\)/);
  assert.match(invite, /history\.replaceState\(null,'',location\.pathname\)/);
  assert.match(invite, /name="referrer" content="no-referrer"/);
});

test("web invite requests approval instead of silently granting membership", () => {
  assert.match(invite, /Enviar solicitação de convidado/);
  assert.match(invite, /\/v1\/guest-applications/);
  assert.match(invite, /Aguarde a aprovação e o provisionamento/);
  assert.match(invite, /Enviar a solicitação não concede acesso à sala/);
});

test("native invite deep link is registered for the application and HTTPS route", () => {
  assert.match(manifest, /android:name="\.MessengerInviteActivity" android:exported="true"/);
  assert.match(manifest, /android:scheme="aibridge" android:host="invite"/);
  assert.match(manifest, /android:scheme="https" android:host="\*\.web\.app" android:pathPrefix="\/i\/"/);
});

test("native invite entry redeems before opening the shared collective room", () => {
  assert.match(native, /redeemGroupInvite\(parts\.conversationId, parts\.token\)/);
  assert.match(native, /getConversation\(parts\.conversationId\)/);
  assert.match(native, /CollectiveRoomActivityV2\.class/);
  assert.match(native, /invite_conversation_id/);
});

test("native group invite rejects non-group and over-capacity rooms", () => {
  assert.match(native, /!"GROUP"\.equals\(kind\)/);
  assert.match(native, /memberCount > 20/);
});
