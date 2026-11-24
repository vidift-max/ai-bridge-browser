import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
const server=await readFile(new URL("../server/http_server.py",import.meta.url),"utf8");
const backend=await readFile(new URL("../server/messenger_backend.py",import.meta.url),"utf8");
test("room admin invite panel exposes bounded expiry and use controls",()=>{
 assert.match(html,/id="invitePanel"[^>]*hidden/);
 assert.match(html,/option value="3600"/);assert.match(html,/option value="86400"/);assert.match(html,/option value="604800"/);
 assert.match(html,/id="inviteUses" type="number" min="1" max="6"/);
 assert.match(html,/expiresInSeconds,maxUses/);
});
test("invite creation requires secure context outside localhost and reveals token only in fragment",()=>{
 assert.match(html,/Convites exigem HTTPS fora do ambiente local/);
 assert.match(html,/\/invite#'\+invite\.inviteId\+'\.'\+invite\.token/);
 assert.match(html,/O segredo só será mostrado nesta tela agora/);
 assert.match(html,/<meta name="referrer" content="no-referrer">|referrerPolicy/);
});
test("invite list renders status and usage without exposing token hashes or secrets",()=>{
 assert.match(html,/\/invites'\);const list=\$\('inviteList'\)/);
 assert.match(html,/invite\.revoked_at/);assert.match(html,/invite\.expires_at/);assert.match(html,/invite\.uses>=invite\.max_uses/);
 assert.match(html,/textContent=status/);
 assert.doesNotMatch(html,/invite\.token_hash|tokenHash/);
});
test("revocation uses the authenticated room-scoped DELETE endpoint",()=>{
 assert.match(html,/\/invites\/\+encodeURIComponent\(invite\.invite_id\),\{method:'DELETE'\}/);
 assert.match(server,/self\.backend\.revoke_room_invite\(\s*self\._auth\(\), parts\[3\], parts\[5\]\)/);
 assert.match(backend,/if not self\._store\.is_conversation_admin\(conversation_id, ai_id\):\s*raise PermissionError\("room_admin_required"\)/);
});
test("invite creation and listing remain server-authorized admin operations",()=>{
 assert.match(server,/self\.backend\.create_room_invite\(/);
 assert.match(server,/self\.backend\.list_room_invites\(self\._auth\(\), invite_path\[3\]\)/);
 assert.match(backend,/self\._store\.is_conversation_admin\(conversation_id, ai_id\)/);
});
test("invite panel is opened only from admin room action",()=>{
 assert.match(html,/if\(room\.isAdmin\)[\s\S]*inviteButton\.onclick=\(\)=>createInvite\(room\)/);
 assert.match(html,/function createInvite\(room\)\{inviteRoom=room/);
});
