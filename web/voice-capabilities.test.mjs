import { readFile } from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";

const source = await readFile(new URL("./voice-capabilities.js", import.meta.url), "utf8");

function loadVoice(overrides = {}) {
  const state = { spoken: [], cancelled: 0, recognition: null };
  class FakeUtterance {
    constructor(text) { this.text = text; }
  }
  class FakeRecognition {
    static async available(options) {
      state.availabilityOptions = options;
      return overrides.availability ?? "available";
    }
    constructor() {
      this.processLocally = false;
      state.recognition = this;
    }
    start() { this.started = true; if (this.onstart) this.onstart(); }
    stop() { this.stopped = true; if (this.onend) this.onend(); }
  }
  const speechSynthesis = {
    speak(utterance) { state.spoken.push(utterance); },
    cancel() { state.cancelled += 1; }
  };
  const window = {
    SpeechRecognition: overrides.noRecognition ? undefined : FakeRecognition,
    SpeechSynthesisUtterance: FakeUtterance,
    speechSynthesis,
    isSecureContext: true,
    ...overrides.window
  };
  vm.runInNewContext(source, { window, Event: class { constructor(type, init) { this.type = type; this.bubbles = init?.bubbles; } } });
  return { api: window.AIBridgeVoice, state, window };
}

test("dictation requires explicit local recognition availability", async () => {
  const { api, state } = loadVoice();
  const capability = await api.inspect();
  assert.equal(capability.dictationAvailable, true);
  assert.equal(state.availabilityOptions.processLocally, true);
  assert.equal(state.availabilityOptions.langs[0], "pt-BR");
});

test("dictation is disabled outside a secure context", async () => {
  const { api } = loadVoice({ window: { isSecureContext: false } });
  const capability = await api.inspect();
  assert.equal(capability.dictationAvailable, false);
  assert.equal(capability.dictationReason, "SECURE_CONTEXT_REQUIRED");
});

test("dictation is disabled when local language pack is not available", async () => {
  const { api } = loadVoice({ availability: "downloadable" });
  const capability = await api.inspect();
  assert.equal(capability.dictationAvailable, false);
  assert.equal(capability.dictationReason, "LOCAL_LANGUAGE_PACK_NOT_AVAILABLE");
  await assert.rejects(
    api.createController().startDictation({ value: "", dispatchEvent() {} }),
    /LOCAL_LANGUAGE_PACK_NOT_AVAILABLE/
  );
});

test("dictation sets processLocally and appends final transcript", async () => {
  const { api, state } = loadVoice();
  const target = { value: "Olá", dispatchEvent(event) { this.lastEvent = event.type; } };
  const controller = api.createController();
  await controller.startDictation(target);
  assert.equal(state.recognition.processLocally, true);
  state.recognition.onresult({
    resultIndex: 0,
    results: [{ isFinal: true, 0: { transcript: " mundo" } }]
  });
  assert.equal(target.value, "Olá mundo");
  assert.equal(target.lastEvent, "input");
  controller.stopDictation();
  assert.equal(state.recognition.stopped, true);
});

test("speech synthesis speaks only on explicit call and can be stopped", () => {
  const { api, state } = loadVoice();
  const controller = api.createController();
  controller.speak("Mensagem de teste");
  assert.equal(state.cancelled, 1);
  assert.equal(state.spoken.length, 1);
  assert.equal(state.spoken[0].text, "Mensagem de teste");
  assert.equal(state.spoken[0].lang, "pt-BR");
  controller.stopSpeech();
  assert.equal(state.cancelled, 2);
});

test("empty text and unavailable synthesis are rejected", () => {
  const { api } = loadVoice();
  const controller = api.createController();
  assert.throws(() => controller.speak("   "), /SPEECH_TEXT_REQUIRED/);
  const unavailable = loadVoice({ window: { speechSynthesis: undefined } }).api.createController();
  assert.throws(() => unavailable.speak("Oi"), /SPEECH_SYNTHESIS_UNAVAILABLE/);
});
