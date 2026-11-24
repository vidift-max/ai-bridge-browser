import {readFile} from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";
const source=await readFile(new URL("./local-ai-model-governance.js",import.meta.url),"utf8");
function load(){const root={};vm.runInNewContext(source,{window:root});return root.AIBridgeLocalAIModelGovernance;}
function valid(){return {schemaVersion:1,modelId:"candidate.example:small",publisher:"Example Publisher",version:"1.0.0",sourceDomain:"models.example.org",artifactSha256:"a".repeat(64),licenseId:"Example-License-1.0",licenseTextReviewed:true,licenseStatus:"APPROVED_FOR_REVIEW",provenanceEvidenceRef:"review-ticket-123",reviews:{provenanceReviewed:true,licenseReviewed:true,securityReviewed:true},userApproval:true,acquisitionStarted:false,executionStarted:false};}
test("valid metadata passes review gate but never authorizes acquisition or execution",()=>{const r=load().validate(valid());assert.equal(r.eligibleForManualApproval,true);assert.equal(r.eligibleForAcquisition,false);assert.equal(r.eligibleForExecution,false);});
test("missing candidate fails closed",()=>{assert.equal(load().validate(null).status,"BLOCKED");});
test("schema and identity are strict",()=>{const c=valid();c.schemaVersion=9;c.modelId="../escape";const r=load().validate(c);assert.ok(r.reasons.includes("UNSUPPORTED_SCHEMA"));assert.ok(r.reasons.includes("INVALID_MODEL_ID"));});
test("publisher version and DNS source domain are required",()=>{const c=valid();c.publisher=" ";c.version="";c.sourceDomain="https://models.example.org/path";const r=load().validate(c);assert.ok(r.reasons.includes("PUBLISHER_REQUIRED"));assert.ok(r.reasons.includes("VERSION_REQUIRED"));assert.ok(r.reasons.includes("SOURCE_DOMAIN_INVALID"));});
test("artifact requires strict SHA-256 hex",()=>{const c=valid();c.artifactSha256="abc";assert.ok(load().validate(c).reasons.includes("SHA256_REQUIRED"));});
test("license text review and approved state are required",()=>{const c=valid();c.licenseTextReviewed=false;c.licenseStatus="UNKNOWN";const r=load().validate(c);assert.ok(r.reasons.includes("LICENSE_TEXT_NOT_REVIEWED"));assert.ok(r.reasons.includes("LICENSE_NOT_APPROVED"));});
test("provenance evidence and independent reviews are required",()=>{const c=valid();c.provenanceEvidenceRef="";c.reviews.securityReviewed=false;const r=load().validate(c);assert.ok(r.reasons.includes("PROVENANCE_EVIDENCE_REQUIRED"));assert.ok(r.reasons.includes("REVIEW_MISSING_SECURITYREVIEWED"));});
test("approval must be explicit boolean true",()=>{for(const a of [false,"true",1,null]){const c=valid();c.userApproval=a;assert.ok(load().validate(c).reasons.includes("EXPLICIT_USER_APPROVAL_REQUIRED"));}});
test("acquisition or execution flags invalidate the record",()=>{const c=valid();c.acquisitionStarted=true;const r=load().validate(c);assert.ok(r.reasons.includes("SIDE_EFFECT_STATE_FORBIDDEN"));assert.equal(r.eligibleForExecution,false);});
test("checklist immutable and module contains no network or persistence calls",()=>{const api=load(),items=api.createReviewChecklist();assert.equal(items.length,6);assert.throws(()=>items.push("bad"));assert.doesNotMatch(source,/\bfetch\s*\(|XMLHttpRequest|WebSocket|localStorage|sessionStorage|indexedDB\.open/);assert.doesNotMatch(source,/https?:\/\//);});
