import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const main = await readFile(new URL("../app/src/main/java/com/vidiftmax/aibridgebrowser/MainActivity.java", import.meta.url), "utf8");
const manifest = await readFile(new URL("../app/src/main/AndroidManifest.xml", import.meta.url), "utf8");
const route = await readFile(new URL("../app/src/main/java/com/vidiftmax/aibridgebrowser/InviteBrowserRoute.java", import.meta.url), "utf8");
const invite = await readFile(new URL("./invite.html", import.meta.url), "utf8");
const rooms = await readFile(new URL("./rooms.html", import.meta.url), "utf8");

test("web Rooms generates the same /invite#id.token shape consumed by invite page", () => {
  assert.match(rooms, /location\.origin\+'\/invite#'\+invite\.inviteId\+'\.'\+invite\.token/);
  assert.match(invite, /location\.hash\.slice\(1\)\.split\('\.'\)/);
  assert.match(invite, /history\.replaceState\(null,'',location\.pathname\)/);
});

test("MainActivity is the Android app-link target for the existing web invite route", () => {
  assert.match(manifest, /android:name="\.MainActivity"[^>]*android:exported="true"/);
  assert.match(manifest, /android:launchMode="singleTop"/);
  assert.match(manifest, /android:host="\*\.web\.app" android:path="\/invite"/);
  assert.match(main, /protected void onNewIntent\(android\.content\.Intent intent\)/);
});

test("incoming invite is validated and loaded in the currently selected WebView", () => {
  const start = main.indexOf("private void openInviteInCurrentTab");
  const end = main.indexOf("private void buildChrome", start);
  const method = main.slice(start, end);
  assert.match(method, /WebView current = currentWebView\(\)/);
  assert.match(method, /current\.loadUrl\(inviteUrl\)/);
  assert.match(main, /InviteBrowserRoute\.toWebUrl/);
});

test("invite browser handoff preserves the fragment for the invite page and rejects query strings", () => {
  assert.match(route, /"\/invite"\.equals\(path\)/);
  assert.match(route, /uri\.getRawFragment\(\)/);
  assert.match(route, /uri\.getRawQuery\(\) != null/);
  assert.match(route, /https:\/\//);
  assert.match(route, /\.web\\\.app/);
});

test("invite handoff does not itself grant room membership", () => {
  assert.match(invite, /Enviar solicitação de convidado/);
  assert.match(invite, /Enviar a solicitação não concede acesso à sala/);
  assert.match(main, /A entrada na sala depende da validação e aprovação do servidor/);
});
