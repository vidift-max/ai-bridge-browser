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
 assert.deepEqual(Array.from(tracker.observe([{conversationId:"a",unreadCount:0},{conversationId:"b",unreadCount:2}],null)),[]);
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
 assert.match(html,/id="inboxNotification"[^>]*aria-live="polite"/);
});

function memoryStorage(){const values=new Map();return{getItem:key=>values.has(key)?values.get(key):null,setItem:(key,value)=>values.set(key,String(value))};}
test("notification center persists records and exposes unread count",()=>{
 const center=api.createCenter(memoryStorage(),"history");
 center.record([{conversationId:"room-a",newCount:2}], "2026-11-24T12:00:00.000Z");
 assert.equal(center.list().length,1);assert.equal(center.unreadCount(),1);
 assert.equal(center.list()[0].conversationId,"room-a");assert.equal(center.list()[0].newCount,2);
});
test("notification center marks one notification read without changing message counts",()=>{
 const center=api.createCenter(memoryStorage(),"history");
 const [item]=center.record([{conversationId:"room-a",newCount:3}]);
 center.markRead(item.id);
 assert.equal(center.unreadCount(),0);assert.equal(center.list()[0].newCount,3);assert.equal(center.list()[0].read,true);
});
test("notification center can mark all notices read",()=>{
 const center=api.createCenter(memoryStorage(),"history");
 center.record([{conversationId:"a",newCount:1},{conversationId:"b",newCount:2}]);
 center.markAllRead();assert.equal(center.unreadCount(),0);assert.ok(center.list().every(item=>item.read));
});
test("notification center caps history and ignores malformed records",()=>{
 const center=api.createCenter(memoryStorage(),"history",2);
 center.record([{conversationId:"a",newCount:1},{conversationId:"b",newCount:1},{conversationId:"c",newCount:1},{conversationId:"",newCount:1}]);
 assert.equal(center.list().length,2);assert.equal(center.list()[0].conversationId,"c");
});
test("notification center validates storage and limits",()=>{
 assert.throws(()=>api.createCenter(null),/invalid_notification_storage/);
 assert.throws(()=>api.createCenter(memoryStorage(),"x",501),/invalid_notification_limit/);
});
test("notification center is identity-scoped and UI exposes history actions",async()=>{
 const storage=memoryStorage(),a=api.createCenter(storage,"identity-a"),b=api.createCenter(storage,"identity-b");
 a.record([{conversationId:"private-a",newCount:1}]);assert.equal(b.list().length,0);
 const {readFile}=await import("node:fs/promises");const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
 assert.match(html,/id="notificationCenter"/);assert.match(html,/id="notificationList"/);
 assert.match(html,/id="markAllNotificationsRead"/);assert.match(html,/data-notification-open/);
});
