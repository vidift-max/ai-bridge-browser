#!/usr/bin/env node
"use strict";

const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const source = fs.readFileSync("app/src/main/assets/ai_bridge_chatgpt_dom_bridge.js", "utf8");

class Node {
  constructor({text="", disabled=false, attrs={}, tagName="DIV"}={}) {
    this.innerText = text;
    this.textContent = text;
    this.disabled = disabled;
    this.attrs = attrs;
    this.tagName = tagName;
    this.value = "";
    this.clicked = false;
    this.events = [];
  }
  focus() {}
  dispatchEvent(event) { this.events.push(event.type); }
  click() { this.clicked = true; }
}

function makeDoc({composer, sendButton, assistants=[], generating=false}) {
  const selectors = new Map();
  selectors.set('[contenteditable="true"][role="textbox"]', []);
  selectors.set('[contenteditable="true"][data-lexical-editor="true"]', []);
  selectors.set('[contenteditable="true"][data-testid*="composer"]', []);
  selectors.set('textarea', []);
  selectors.set('[contenteditable="true"]', []);
  selectors.set('button[data-testid="send-button"]', []);
  selectors.set('button[aria-label*="Send prompt" i]', []);
  selectors.set('button[aria-label*="Enviar" i]', []);
  selectors.set('button[type="submit"]', []);
  selectors.set('[data-message-author-role="assistant"]', assistants);
  selectors.set('div[data-testid^="conversation-turn-"] [data-message-author-role="assistant"]', assistants);
  if (composer) {
    if (composer.tagName === "TEXTAREA") selectors.set("textarea", [composer]);
    else selectors.set('[contenteditable="true"][role="textbox"]', [composer]);
  }
  if (sendButton) selectors.set('button[data-testid="send-button"]', [sendButton]);
  if (generating) selectors.set('button[aria-label*="Stop" i]', [new Node()]);
  return {
    body: {innerText: assistants.map(x=>x.innerText).join("\n")},
    querySelector(selector) { return (selectors.get(selector)||[])[0] || null; },
    querySelectorAll(selector) { return selectors.get(selector)||[]; }
  };
}

const sandbox = {
  window: {},
  globalThis: {},
  InputEvent: class { constructor(type, init={}) { this.type=type; Object.assign(this, init); } },
  Event: class { constructor(type) { this.type=type; } }
};
sandbox.window = sandbox;
vm.runInNewContext(source, sandbox);

{
  const composer = new Node({tagName:"DIV"});
  const button = new Node({tagName:"BUTTON"});
  const doc = makeDoc({composer, sendButton:button});
  const result = sandbox.AIBridgeChatGPTDomBridge.prepareAndSend(doc, "hello AI-02");
  assert.strictEqual(result.ok, true);
  assert.strictEqual(result.code, "SUBMITTED");
  assert.strictEqual(composer.textContent, "hello AI-02");
  assert.deepStrictEqual(composer.events, ["input","change"]);
  assert.strictEqual(button.clicked, true);
}

{
  const textarea = new Node({tagName:"TEXTAREA"});
  const button = new Node({tagName:"BUTTON"});
  const doc = makeDoc({composer:textarea, sendButton:button});
  const result = sandbox.AIBridgeChatGPTDomBridge.prepareAndSend(doc, "hello");
  assert.strictEqual(result.code, "SUBMITTED");
  assert.strictEqual(textarea.value, "hello");
  assert.strictEqual(button.clicked, true);
}

{
  const first = new Node({text:"old answer"});
  const latest = new Node({text:"new answer"});
  const doc = makeDoc({assistants:[first, latest]});
  const inspected = sandbox.AIBridgeChatGPTDomBridge.inspect(doc);
  assert.strictEqual(inspected.latestAssistant, "new answer");
}

{
  const doc = makeDoc({composer:null, sendButton:null});
  const result = sandbox.AIBridgeChatGPTDomBridge.prepareAndSend(doc, "blocked");
  assert.strictEqual(result.code, "COMPOSER_NOT_FOUND");
}

console.log("chatgpt-dom-bridge: 4/4 PASS");
