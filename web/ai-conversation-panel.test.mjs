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
 dispatch(k){for(const fn of this.listeners[k]||[])fn({preventDefault(){}});}
 remove(){this.removed=true;}
 insertBefore(child){this.children.push(child);}
}
function fixture({privateRoom=true,host=false}={}){
 const section=new Element(),composer=new Element();composer.id="composer";
 const doc={createElement:tag=>new Element(tag),getElementById:id=>id==="conversation"?section:id==="composer"?composer:null};
 const scope={window:{document:doc}};vm.runInNewContext(source,scope);
 let ctx={room:{conversationId:"p1",kind:privateRoom?"PRIVATE":"GROUP",memberAiIds:["A","B"]},identity:{aiId:"A"}};
 if(host)scope.window.AIBridgeAgentHost={requestAgent:async()=>({}),verifyAttestation:async()=>true};
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
test("panel dispose removes only its own panel",()=>{
 const f=fixture();f.panel.dispose();assert.equal(f.panel.getElement().removed,true);
});
