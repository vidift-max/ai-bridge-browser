import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const invite = await readFile(new URL("./invite.html", import.meta.url), "utf8");
const intakeTest = await readFile(new URL("../server/test_guest_intake_http.py", import.meta.url), "utf8");
const backend = await readFile(new URL("../server/messenger_backend.py", import.meta.url), "utf8");
const http = await readFile(new URL("../server/http_server.py", import.meta.url), "utf8");

test("successful invite submission renders a pending receipt with application reference", () => {
  assert.match(invite, /id="receipt" hidden aria-live="polite"/);
  assert.match(invite, /application\.status!=='PENDING'/);
  assert.match(invite, /application\.applicationId/);
  assert.match(invite, /Código de acompanhamento:/);
});

test("receipt states that approval and provisioning remain required and no access is granted", () => {
  assert.match(invite, /application\.accessGranted!==false/);
  assert.match(invite, /application\.providerVerified!==false/);
  assert.match(invite, /O administrador ainda precisa aprovar e provisionar/);
  assert.match(invite, /Nenhum acesso foi concedido/);
});

test("successful submission disables duplicate submission and locks identity claims", () => {
  assert.match(invite, /button\.textContent='Solicitação enviada'/);
  assert.match(invite, /nameInput\.disabled=true/);
  assert.match(invite, /providerInput\.disabled=true/);
  assert.match(invite, /catch\(error\).*button\.disabled=false/);
});

test("server returns a pending application receipt without issuing a credential", () => {
  assert.match(intakeTest, /self\.assertEqual\(data\["application"\]\["status"\], "PENDING"\)/);
  assert.match(intakeTest, /self\.assertFalse\(data\["application"\]\["accessGranted"\]\)/);
  assert.match(backend, /"applicationId": row\["application_id"\]/);
  assert.match(http, /"applicationId": result\["applicationId"\]/);
  assert.match(http, /"accessGranted": False/);
});

test("public receipt contains no guest session token or credential and does not imply live polling", () => {
  assert.doesNotMatch(invite, /sessionToken|bearerToken|guestCredential/);
  assert.match(invite, /Esta página não consulta o estado automaticamente/);
  assert.match(invite, /history\.replaceState\(null,'',location\.pathname\)/);
});
