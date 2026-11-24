import test from "node:test";
import assert from "node:assert/strict";
import "../web/ai-room-notifications.js";
const api=globalThis.AIBridgeRoomNotifications;
test("initial inbox snapshot establishes baseline without false notifications",()=>{
 const tracker=api.createTracker();
 assert.deepEqual(Array.from(tracker.observe([{conversationId:"a",unreadCount:4}],null)),[]);
});
test("only increases in unread counts produce notification events",()=>{
 const tracker=api.createTracker();tracker.observe([{conversationId:"a",unreadCount:1}],null);
 const events=tracker.observe([{conversationId:"a",unreadCount:3}],null);
 assert.deepEqual(Array.from(events),[{conversationId:"a",newCount:2,totalUnread:3}]);
});
test("decreases reset baseline and later increases are detected",()=>{
 const tracker=api.createTracker();tracker.observe([{conversationId:"a",unreadCount:4}],null);
 assert.deepEqual(Array.from(tracker.observe([{conversationId:"a",unreadCount:0}],null)),[]);
 assert.equal(tracker.observe([{conversationId:"a",unreadCount:1}],null)[0].newCount,1);
});
test("active conversation does not generate a new-message notification",()=>{
 const tracker=api.createTracker();tracker.observe([{conversationId:"a",unreadCount:0}],null);
 assert.deepEqual(Array.from(tracker.observe([{conversationId:"a",unreadCount:2}],"a")),[]);
});
test("new conversations do not create false positive notifications",()=>{
 const tracker=api.createTracker();tracker.observe([{conversationId:"a",unreadCount:0}],null);
 assert.deepEqual(Array.from(tracker.observe([{conversationId:"a",unreadCount:3},{conversationId:"b",unreadCount:2}],null)),[]);
});
test("multiple conversations are aggregated and formatted",()=>{
 const tracker=api.createTracker();tracker.observe([{conversationId:"a",unreadCount:0},{conversationId:"b",unreadCount:0}],null);
 const events=tracker.observe([{conversationId:"a",unreadCount:2},{conversationId:"b",unreadCount:1}],null);
 assert.equal(api.format(events),"3 novas mensagens em 2 conversas");
});
test("invalid inbox input is rejected and reset starts a new baseline",()=>{
 const tracker=api.createTracker();assert.throws(()=>tracker.observe(null,null),/invalid_notification_inbox/);
 tracker.observe([{conversationId:"a",unreadCount:0}],null);tracker.reset();
 assert.deepEqual(Array.from(tracker.observe([{conversationId:"a",unreadCount:5}],null)),[]);
});
test("rooms UI integrates notification tracker and non-invasive browser notifications",async()=>{
 const {readFile}=await import("node:fs/promises");const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
 assert.match(html,/ai-room-notifications\.js/);
 assert.match(html,/notificationTracker\.observe\(page\.rooms,activeRoom\?\.conversationId\)/);
 assert.match(html,/Notification\.permission==='granted'/);
 assert.match(html,/inboxPollTimer=setInterval/);
 assert.match(html,/aria-live="polite" id="inboxNotification"/);
});
