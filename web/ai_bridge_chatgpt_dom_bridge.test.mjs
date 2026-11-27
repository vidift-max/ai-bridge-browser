import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import {readFile} from "node:fs/promises";

const source=await readFile(new URL("../app/src/main/assets/ai_bridge_chatgpt_dom_bridge.js",import.meta.url),"utf8");

function element({tagName="DIV",text="",disabled=false}={}){
  return {tagName,innerText:text,textContent:text,disabled,focus(){},click(){this.clicked=true;},
    dispatchEvent(){},value:"",querySelectorAll(){return []}};
}

function fixture({assistant=["old"],hasComposer=true,hasSend=true,generating=false}={}){
  const textarea=hasComposer?element({tagName:"TEXTAREA"}):null;
  const send=hasSend?element({tagName:"BUTTON"}):null;
  if(send)send.dataset={testid:"send-button"};
  const assistants=assistant.map(text=>element({text}));
  const doc={
    body:{innerText:"body"},
    querySelector(selector){
      if(selector==='textarea')return textarea;
      if(selector==='[contenteditable="true"][role="textbox"]')return null;
      if(selector==='[contenteditable="true"]')return null;
      if(selector.includes("data-testid")&&hasSend)return send;
      if(selector.includes("aria-label")&&generating)return send;
      return null;
    },
    querySelectorAll(selector){
      if(selector==='[data-message-author-role="assistant"]')return assistants;
      return [];
    }
  };
  const scope={window:{},HTMLTextAreaElement:function(){},InputEvent:function(){},Event:function(){}};
  Object.defineProperty(scope.HTMLTextAreaElement.prototype,"value",{set(v){Object.defineProperty(this,"value",{value:v,writable:true,configurable:true});}});
  vm.runInNewContext(source,scope);
  return {bridge:scope.window.AIBridgeChatGPTDomBridge,doc,textarea,send};
}

test("inspect reports composer, send control and latest assistant",()=>{
  const f=fixture({assistant:["primeira","última"]});
  const result=f.bridge.inspect(f.doc);
  assert.equal(result.composer,true);
  assert.equal(result.sendButton,true);
  assert.equal(result.latestAssistant,"última");
});

test("prepareAndSend writes the prompt and clicks send",()=>{
  const f=fixture();
  const result=f.bridge.prepareAndSend(f.doc,"Olá AI-02");
  assert.equal(result.code,"SUBMITTED");
  assert.equal(f.textarea.value,"Olá AI-02");
  assert.equal(f.send.clicked,true);
});

test("bridge fails closed when composer is unavailable",()=>{
  const f=fixture({hasComposer:false});
  const result=f.bridge.prepareAndSend(f.doc,"x");
  assert.equal(result.ok,false);
  assert.equal(result.code,"COMPOSER_NOT_FOUND");
});

test("bridge fails closed when send control is unavailable",()=>{
  const f=fixture({hasSend:false});
  const result=f.bridge.prepareAndSend(f.doc,"x");
  assert.equal(result.ok,false);
  assert.equal(result.code,"SEND_BUTTON_NOT_FOUND");
});

test("inspect exposes generating state without treating it as a completed response",()=>{
  const f=fixture({generating:true});
  const result=f.bridge.inspect(f.doc);
  assert.equal(result.generating,true);
});
