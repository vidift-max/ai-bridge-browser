import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
const server=await readFile(new URL("../server/http_server.py",import.meta.url),"utf8");
const backend=await readFile(new URL("../server/messenger_backend.py",import.meta.url),"utf8");
const store=await readFile(new URL("../server/sqlite_store.py",import.meta.url),"utf8");
test("admin join request panel is hidden by default and has explicit close control",()=>{
 assert.match(html,/id="requestPanel" class="request-panel" hidden/);
 assert.match(html,/id="closeRequests"/);
 assert.match(html,/requestRoom=room;\$\('requestPanel'\)\.hidden=false/);
});
test("pending requests are rendered as text with explicit approve and reject actions",()=>{
 assert.match(html,/request\.status!=='PENDING'/);
 assert.match(html,/identity\.textContent=request\.ai_id/);
 assert.match(html,/button\.textContent=decision==='APPROVE'\?'Aprovar':'Recusar'/);
 assert.match(html,/meta\.textContent='Solicitação recebida em '/);
 assert.doesNotMatch(html,/window\.confirm\('A IA '/);
});
test("decision action is room-scoped, one-at-a-time, and checks authoritative response",()=>{
 assert.match(html,/requestRoom\?\.conversationId!==room\.conversationId/);
 assert.match(html,/buttons\.forEach\(item=>item\.disabled=true\)/);
 assert.match(html,/join-requests\/'.*\/decision/);
 assert.match(html,/\['APPROVED','REJECTED'\]\.includes\(status\)/);
 assert.match(html,/buttons\.forEach\(item=>item\.disabled=false\)/);
});
test("only pending requests are shown and successful decisions update visible state",()=>{
 assert.match(html,/status==='APPROVED'\?'Aprovada':'Recusada'/);
 assert.match(html,/if\(status==='APPROVED'\)await loadRooms\(\)/);
 assert.match(html,/Nenhuma solicitação pendente nesta sala/);
});
test("server listing and decision endpoints are backed by authenticated admin authorization",()=>{
 assert.match(server,/self\.backend\.list_join_requests\(self\._auth\(\), invite_parts\[3\]\)/);
 assert.match(server,/self\.backend\.decide_join_request\(/);
 assert.match(backend,/def list_join_requests[\s\S]{0,300}is_conversation_admin\(conversation_id, ai_id\)/);
 assert.match(backend,/def decide_join_request[\s\S]{0,300}is_conversation_admin\(conversation_id, ai_id\)/);
});
test("backend decision accepts only APPROVE or REJECT and handles stale decisions",()=>{
 assert.match(backend,/decision not in \("APPROVE", "REJECT"\)/);
 assert.match(backend,/request_already_decided/);
 assert.match(store,/BEGIN IMMEDIATE/);
 assert.ok(store.includes('row["status"] != "PENDING"'));
});
test("room admin action opens the review panel without auto-deciding requests",()=>{
 assert.match(html,/requestsButton\.onclick=\(\)=>reviewRequests\(room\)/);
 assert.match(html,/async function reviewRequests\(room\)/);
 assert.match(html,/async function decideJoinRequest\(room,request,decision,button\)/);
});
