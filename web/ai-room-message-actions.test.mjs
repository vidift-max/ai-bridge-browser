import test from "node:test";
import assert from "node:assert/strict";
import "../web/ai-room-message-actions.js";
const actions=globalThis.AIBridgeRoomMessageActions;

test("copyMessage writes the exact message text to the supplied clipboard",async()=>{
 let copied=null;
 const clipboard={writeText:async value=>{copied=value}};
 assert.equal(await actions.copyMessage("  Keep original spacing  ",clipboard),true);
 assert.equal(copied,"  Keep original spacing  ");
});
test("copyMessage rejects empty and non-string message bodies",async()=>{
 const clipboard={writeText:async()=>{}};
 await assert.rejects(actions.copyMessage("",clipboard),/ROOM_MESSAGE_TEXT_REQUIRED/);
 await assert.rejects(actions.copyMessage(null,clipboard),/ROOM_MESSAGE_TEXT_REQUIRED/);
});
test("copyMessage reports unavailable clipboard without pretending success",async()=>{
 await assert.rejects(actions.copyMessage("message",null),/CLIPBOARD_UNAVAILABLE/);
 await assert.rejects(actions.copyMessage("message",{}),/CLIPBOARD_UNAVAILABLE/);
});
test("copyMessage propagates clipboard permission failures",async()=>{
 const clipboard={writeText:async()=>{throw new Error("permission denied")}};
 await assert.rejects(actions.copyMessage("message",clipboard),/permission denied/);
});
test("room UI exposes an accessible copy action without unsafe HTML rendering",async()=>{
 const {readFile}=await import("node:fs/promises");
 const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
 const server=await readFile(new URL("../server/http_server.py",import.meta.url),"utf8");
 assert.match(html,/ai-room-message-actions\.js/);
 assert.match(html,/AIBridgeRoomMessageActions\.copyMessage/);
 assert.match(html,/Copiar mensagem/);
 assert.doesNotMatch(html,/innerHTML/);
 assert.match(server,/ai-room-message-actions\.js/);
});
