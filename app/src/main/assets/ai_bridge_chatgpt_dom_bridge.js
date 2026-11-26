(function(root){
 "use strict";
 const MAX_TEXT=12000;
 function clean(value){return String(value||"").replace(/\u00a0/g," ").replace(/[ \t]+\n/g,"\n").replace(/\n{3,}/g,"\n\n").trim();}
 function latestAssistant(doc){
  const selectors=[
   '[data-message-author-role="assistant"]',
   'div[data-testid^="conversation-turn-"] [data-message-author-role="assistant"]'
  ];
  for(const selector of selectors){
   const nodes=Array.from(doc.querySelectorAll(selector));
   for(let i=nodes.length-1;i>=0;i--){
    const text=clean(nodes[i].innerText||nodes[i].textContent);
    if(text)return text.slice(-MAX_TEXT);
   }
  }
  return "";
 }
 function composer(doc){
  return doc.querySelector('textarea') ||
    doc.querySelector('[contenteditable="true"][role="textbox"]') ||
    doc.querySelector('[contenteditable="true"]');
 }
 function sendButtonElement(doc){
  const selectors=[
   'button[data-testid="send-button"]',
   'button[aria-label*="Send prompt" i]',
   'button[aria-label*="Enviar" i]',
   'button[type="submit"]'
  ];
  for(const selector of selectors){
   const button=doc.querySelector(selector);
   if(button)return button;
  }
  return null;
 }
 function sendButton(doc){
  const button=sendButtonElement(doc);
  return button&&!button.disabled?button:null;
 }
 function setComposerValue(node,text){
  const value=String(text||"");
  node.focus();
  if(node.tagName==="TEXTAREA"){
   const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,"value")?.set;
   if(setter)setter.call(node,value);else node.value=value;
  }else{
   node.textContent=value;
  }
  node.dispatchEvent(new InputEvent("input",{bubbles:true,inputType:"insertText",data:value}));
  node.dispatchEvent(new Event("change",{bubbles:true}));
 }
 function inspect(doc){
  const box=composer(doc), button=sendButton(doc);
  const body=clean(doc.body?.innerText||"");
  const generating=!!doc.querySelector('button[aria-label*="Stop" i],button[aria-label*="Parar" i],[data-testid*="stop-button"]');
  return {ok:true,composer:!!box,sendButton:!!sendButtonElement(doc),sendButtonEnabled:!!button,generating,latestAssistant:latestAssistant(doc),bodyTail:body.slice(-2000)};
 }
 function prepareAndSend(doc,text){
  const box=composer(doc);
  if(!box) return {ok:false,code:"COMPOSER_NOT_FOUND"};
  setComposerValue(box,text);
  const button=sendButton(doc);
  if(!button)return {ok:false,code:"SEND_BUTTON_NOT_FOUND"};
  button.click();
  return {ok:true,code:"SUBMITTED"};
 }
 root.AIBridgeChatGPTDomBridge=Object.freeze({inspect,prepareAndSend,latestAssistant});
})(typeof window!=="undefined"?window:globalThis);
