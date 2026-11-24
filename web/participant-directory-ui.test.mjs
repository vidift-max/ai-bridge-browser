import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
const server=await readFile(new URL("../server/http_server.py",import.meta.url),"utf8");
const backend=await readFile(new URL("../server/messenger_backend.py",import.meta.url),"utf8");
const presence=await readFile(new URL("../server/presence_service.py",import.meta.url),"utf8");
test("participant directory exposes accessible counts, filters and explicit refresh",()=>{
 assert.match(html,/id="participantPanel"/);
 assert.match(html,/id="participantCounts"[^>]*aria-live="polite"/);
 assert.match(html,/id="participantFilter"/);
 assert.match(html,/option value="ONLINE"/);
 assert.match(html,/option value="OFFLINE"/);
 assert.match(html,/option value="ACTIVE"/);
 assert.match(html,/id="refreshParticipants"/);
});
test("participant cards show server identity, internal number, presence and last activity",()=>{
 assert.match(html,/person\.internalNumber/);
 assert.match(html,/person\.displayName/);
 assert.match(html,/person\.aiId/);
 assert.match(html,/person\.status==='ONLINE'/);
 assert.match(html,/person\.activeInRoom/);
 assert.match(html,/person\.lastSeenAt/);
 assert.match(html,/name\.textContent=/);
 assert.match(html,/id\.textContent=/);
 assert.match(html,/seen\.textContent=/);
 assert.doesNotMatch(html,/card\.innerHTML/);
});
test("presence filters distinguish all, online, offline and active-in-room participants",()=>{
 assert.match(html,/filter==='ALL'/);
 assert.match(html,/filter==='ACTIVE'\?person\.activeInRoom:person\.status===filter/);
 assert.match(html,/Nenhum participante corresponde a este filtro/);
 assert.match(html,/participantSnapshot\.filter\(person=>person\.status==='ONLINE'\)/);
 assert.match(html,/participantSnapshot\.filter\(person=>person\.activeInRoom\)/);
});
test("refresh is room-scoped and ignores late responses from a previously selected room",()=>{
 assert.match(html,/const roomId=activeRoom\.conversationId/);
 assert.match(html,/activeRoom\.conversationId!==roomId/);
 assert.match(html,/button\.disabled=true;try\{await loadPresence\(\)/);
 assert.match(html,/finally\{button\.disabled=false\}/);
});
test("directory refresh continues using authenticated server-owned membership identities",()=>{
 assert.match(server,/self\.backend\.list_conversation_identities\(/);
 assert.match(server,/self\.backend\.assert_authenticated_principal\(self\._auth\(\), principal\)/);
 assert.match(backend,/def list_conversation_identities[\s\S]{0,240}self\.authorize_member\(ai_id, conversation_id\)/);
 assert.match(backend,/self\._identities\.list_members\(members\)/);
 assert.match(backend,/self\._presence\.list_room\(conversation_id, members\)/);
});
test("online and active-in-room indicators follow server TTL presence semantics",()=>{
 assert.match(presence,/DEFAULT_TTL_SECONDS = 90/);
 assert.match(presence,/row\["last_seen"\] >= timestamp - self\._ttl_seconds/);
 assert.match(presence,/bool\(online and row\["active_here"\]\)/);
 assert.match(html,/person\.status==='ONLINE'\?'ONLINE':'OFFLINE'/);
 assert.match(html,/person\.status==='ONLINE'&&person\.activeInRoom===true/);
});
test("filter and refresh handlers update the participant directory without mutating membership",()=>{
 assert.match(html,/participantFilter'\)\.addEventListener\('change',renderParticipants\)/);
 assert.match(html,/refreshParticipants'\)\.addEventListener\('click'/);
 assert.doesNotMatch(html,/DELETE \/v1\/conversations.*identities/);
});
