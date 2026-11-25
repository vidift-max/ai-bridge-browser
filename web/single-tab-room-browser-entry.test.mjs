import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const main = await readFile(new URL("../app/src/main/java/com/vidiftmax/aibridgebrowser/MainActivity.java", import.meta.url), "utf8");
const route = await readFile(new URL("../app/src/main/java/com/vidiftmax/aibridgebrowser/CollectiveRoomBrowserRoute.java", import.meta.url), "utf8");

test("browser chrome exposes a collective room action", () => {
  assert.match(main, /collectiveRoom\.setText\("Sala coletiva"\)/);
  assert.match(main, /collectiveRoom\.setContentDescription\("Abrir a conversa coletiva na aba atual"\)/);
});

test("room shortcut reuses the current WebView instead of creating a tab", () => {
  const start = main.indexOf("private void openCollectiveRoom()");
  const end = main.indexOf("private void promptCollectiveRoomUrl", start);
  const method = main.slice(start, end);
  assert.match(method, /WebView current = currentWebView\(\)/);
  assert.match(method, /current\.loadUrl\(validated\)/);
  assert.doesNotMatch(method, /addTab\(/);
});

test("room URL is user-configured, validated and persisted", () => {
  assert.match(main, /PREF_COLLECTIVE_ROOMS_URL/);
  assert.match(main, /CollectiveRoomBrowserRoute\.validate/);
  assert.match(main, /putString\(PREF_COLLECTIVE_ROOMS_URL, validated\)/);
  assert.match(main, /promptCollectiveRoomUrl\(configured\)/);
});

test("shortcut does not bypass the browser HTTPS navigation policy", () => {
  assert.match(route, /"https"\.equalsIgnoreCase\(scheme\)/);
  assert.match(route, /uri\.getRawUserInfo\(\) != null/);
  assert.match(route, /uri\.getRawQuery\(\) != null/);
  assert.match(route, /uri\.getRawFragment\(\) != null/);
  assert.match(route, /path\.equals\("\/rooms"\) \|\| path\.equals\("\/rooms\.html"\)/);
});
