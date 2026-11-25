import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("./gpt6-messenger.html", import.meta.url), "utf8");

test("GPT-6 messenger targets the collective room endpoint", () => {
  assert.match(html, /id="conversationId"/);
  assert.match(html, /\/v1\/gpt6\/room\/respond/);
  assert.match(html, /clientRequestId/);
  assert.match(html, /assistantMessage\?\.body/);
});

test("GPT-6 messenger does not claim the private ChatGPT session is connected", () => {
  assert.match(html, /não é a sessão privada do ChatGPT/);
  assert.doesNotMatch(html, /const online=!!d\.assistant\?\.online/);
});

test("GPT-6 messenger keeps provider credentials server-side", () => {
  assert.match(html, /Bearer '\+token/);
  assert.doesNotMatch(html, /OPENAI_API_KEY/);
  assert.doesNotMatch(html, /api\.openai\.com/);
});
