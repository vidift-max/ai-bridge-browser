import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const invite = await readFile(new URL("./invite.html", import.meta.url), "utf8");
const intakeTest = await readFile(new URL("../server/test_guest_intake_http.py", import.meta.url), "utf8");
const backend = await readFile(new URL("../server/messenger_backend.py", import.meta.url), "utf8");
const http = await readFile(new URL("../server/http_server.py", import.meta.url), "utf8");

test("successful invite submission renders a pending receipt with application reference", () => {
  assert.match(invite, /id="receipt" hidden aria-live="polite"/);
  assert.match(invite, /includes\(application\.status\)/);
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
  assert.match(invite, /Acompanhamento temporário ativo nesta aba/);
  assert.match(invite, /history\.replaceState\(null,'',location\.pathname\)/);
});

test("status capability is generated with Web Crypto and kept only in the live page", () => {
  assert.match(invite, /crypto\.getRandomValues\(new Uint8Array\(32\)\)/);
  assert.match(invite, /let statusCapability=null/);
  assert.match(invite, /statusCapability\}\)/);
  assert.doesNotMatch(invite, /localStorage|sessionStorage|document\.cookie/);
  assert.match(invite, /replaceAll\('\+','-'\)\.replaceAll\('\/','_'\)/);
});

test("invite page calls the read-only status endpoint with bounded polling", () => {
  assert.match(invite, /\/v1\/guest-applications\/status/);
  assert.match(invite, /attempt<6/);
  assert.match(invite, /statusEl\.textContent='Estado atualizado: '\+state/);
  assert.match(invite, /A consulta não concede acesso à sala/);
});

test("in-tab retries reuse one immutable payload and cannot bind the capability to another name", () => {
  assert.match(invite, /let pendingSubmission=null/);
  assert.match(invite, /pendingSubmission=\{inviteToken,displayName,providerClaim:providerInput\.value,statusCapability\}/);
  assert.match(invite, /JSON\.stringify\(pendingSubmission\)/);
  assert.match(invite, /nameInput\.disabled=true;providerInput\.disabled=true/);
});
