import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import {readFile} from "node:fs/promises";
const source=await readFile(new URL("./ai-conversation-panel.js",import.meta.url),"utf8");
class Element{
 constructor(tag="div"){this.tagName=tag;this.children=[];this.listeners={};this.attributes={};this.value="";this.textContent="";this.disabled=false;this.hidden=false;this.id="";this.className="";this.selected=false;this.maxLength=0;}
 append(...items){this.children.push(...items);}
 setAttribute(k,v){this.attributes[k]=v;}
 addEventListener(k,fn){(this.listeners[k]||(this.listeners[k]=[])).push(fn);}
 async dispatch(k){for(const fn of this.listeners[k]||[])await fn({preventDefault(){}});}
 remove(){this.removed=true;}
 insertBefore(child){this.children.push(child);}
}
function fixture({privateRoom=true,host=false}={}){
 const section=new Element(),composer=new Element();composer.id="composer";
 const doc={createElement:tag=>new Element(tag),getElementById:id=>id==="conversation"?section:id==="composer"?composer:null};
 const scope={window:{document:doc}};vm.runInNewContext(source,scope);
 let ctx={room:{conversationId:"p1",kind:privateRoom?"PRIVATE":"GROUP",memberAiIds:["A","B"]},identity:{aiId:"A"}};
 if(host)scope.window.AIBridgeAgentHost={requestAgent:async()=>({}),verifyAttestation:async()=>true,registerSession:async()=>({aiId:"A",ttlSeconds:1800})};
 const shown=[];
 const panel=scope.window.AIBridgeConversationPanel.create({document:doc,getContext:()=>ctx,onMessage:async m=>shown.push(m)});
 return {panel,section,scope,setContext:v=>ctx=v};
}
test("panel mounts into Rooms and defaults to safe blocked state without provider host",()=>{
 const f=fixture();assert.equal(f.section.children.length,1);assert.equal(f.panel.getElement().id,"aiConversationPanel");
 const start=f.panel.getElement().children[3].children[1];assert.equal(start.disabled,true);
});
test("panel enables only for a two-member private room with authenticated host",()=>{
 const f=fixture({host:true});const start=f.panel.getElement().children[3].children[1];assert.equal(start.disabled,false);
 f.setContext({room:{conversationId:"g",kind:"GROUP",memberAiIds:["A","B"]},identity:{aiId:"A"}});
 f.panel.setContext();assert.equal(start.disabled,true);
});
test("panel blocks rooms with more than two members",()=>{
 const f=fixture({host:true});f.setContext({room:{conversationId:"p",kind:"PRIVATE",memberAiIds:["A","B","C"]},identity:{aiId:"A"}});
 f.panel.setContext();assert.equal(f.panel.getElement().children[3].children[1].disabled,true);
});
test("panel exposes bounded turn choices and stop control starts disabled",()=>{
 const f=fixture();const controls=f.panel.getElement().children[3];
 assert.deepEqual(controls.children[0].children.map(x=>x.value),["2","4","6","8","10","12","16","20"]);
 assert.equal(controls.children[2].disabled,true);
});
test("Rooms loads the controller, adapter, runtime and panel assets in dependency order",async()=>{
 const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
 const ordered=["/ai-conversation-loop.js","/ai-agent-adapter.js","/ai-conversation-runtime.js","/ai-conversation-host-client.js","/ai-conversation-panel.js"];
 let previous=-1;
 for(const asset of ordered){const index=html.indexOf('<script src="'+asset+'"></script>');assert.ok(index>previous,asset+" must load after its dependency");previous=index;}
});
test("Rooms mounts the conversation panel only after opening a selected room",async()=>{
 const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
 assert.match(html,/function ensureConversationPanel\(\)/);
 assert.match(html,/ensureConversationPanel\(\)\.setContext\(\)/);
 assert.match(html,/onMessage:\(message\)=>addMessage\(message,message\.senderAiId===identity\?\.aiId\)/);
});
test("Rooms does not create a fake provider host or automatically start a run",async()=>{
 const html=await readFile(new URL("./rooms.html",import.meta.url),"utf8");
 assert.doesNotMatch(html,/AIBridgeAgentHost\s*=\s*\{/);
 assert.doesNotMatch(html,/\.start\(\{firstMessage:/);
});

test("panel starts only after explicit click and passes the selected turn limit",async()=>{
 const f=fixture({host:true});
 const calls=[];
 f.scope.window.AIBridgeConversationRuntime={create:options=>({start:async config=>{calls.push(config);options.onState({state:"RUNNING",turnsCompleted:0,maxTurns:config.maxTurns});await options.onMessage({conversationId:"p1",senderAiId:"B",recipientAiId:"A",body:"reply",turn:1});return {turnsCompleted:config.maxTurns};},stop:()=>{},snapshot:()=>({turnsCompleted:0})})};
 const children=f.panel.getElement().children, prompt=children[2],controls=children[3];
 prompt.value="hello";controls.children[0].value="8";
 await controls.children[1].dispatch("click");
 assert.equal(calls.length,1);assert.equal(calls[0].firstMessage,"hello");assert.equal(calls[0].maxTurns,8);
});
test("panel explicitly registers the current AI session before a peer test",async()=>{
 const f=fixture({host:true});const controls=f.panel.getElement().children[3];
 await controls.children[3].dispatch("click");
 assert.match(f.panel.getElement().children[4].textContent,/Sessão registrada para A/);
});

test("panel dispose removes only its own panel",()=>{
 const f=fixture();f.panel.dispose();assert.equal(f.panel.getElement().removed,true);
});
