(function(root) {
"use strict";
var HEX_SHA256=/^[a-f0-9]{64}$/;
var SAFE_ID=/^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$/;
var REQUIRED=["provenanceReviewed","licenseReviewed","securityReviewed"];
function blocked(reasons){return Object.freeze({status:"BLOCKED",eligibleForManualApproval:false,eligibleForAcquisition:false,eligibleForExecution:false,reasons:Object.freeze(reasons)});}
function validate(c){
var r=[];
if(!c||typeof c!=="object"||Array.isArray(c))return blocked(["CANDIDATE_METADATA_REQUIRED"]);
if(c.schemaVersion!==1)r.push("UNSUPPORTED_SCHEMA");
if(typeof c.modelId!=="string"||!SAFE_ID.test(c.modelId))r.push("INVALID_MODEL_ID");
if(typeof c.publisher!=="string"||c.publisher.trim().length<2||c.publisher.length>120)r.push("PUBLISHER_REQUIRED");
if(typeof c.version!=="string"||!SAFE_ID.test(c.version))r.push("VERSION_REQUIRED");
if(typeof c.sourceDomain!=="string"||!/^(?:[a-z0-9-]+\.)+[a-z]{2,}$/i.test(c.sourceDomain)||c.sourceDomain.length>253)r.push("SOURCE_DOMAIN_INVALID");
if(typeof c.artifactSha256!=="string"||!HEX_SHA256.test(c.artifactSha256))r.push("SHA256_REQUIRED");
if(typeof c.licenseId!=="string"||c.licenseId.trim().length<2||c.licenseId.length>100)r.push("LICENSE_IDENTIFIER_REQUIRED");
if(c.licenseTextReviewed!==true)r.push("LICENSE_TEXT_NOT_REVIEWED");
if(c.licenseStatus!=="APPROVED_FOR_REVIEW")r.push("LICENSE_NOT_APPROVED");
if(typeof c.provenanceEvidenceRef!=="string"||c.provenanceEvidenceRef.trim().length<3||c.provenanceEvidenceRef.length>200)r.push("PROVENANCE_EVIDENCE_REQUIRED");
if(!c.reviews||typeof c.reviews!=="object"||Array.isArray(c.reviews))r.push("REVIEW_ATTESTATIONS_REQUIRED");
else REQUIRED.forEach(function(k){if(c.reviews[k]!==true)r.push("REVIEW_MISSING_"+k.toUpperCase());});
if(c.userApproval!==true)r.push("EXPLICIT_USER_APPROVAL_REQUIRED");
if(c.acquisitionStarted===true||c.executionStarted===true)r.push("SIDE_EFFECT_STATE_FORBIDDEN");
if(r.length)return blocked(r);
return Object.freeze({status:"METADATA_REVIEW_COMPLETE_PENDING_SEPARATE_ACTION",eligibleForManualApproval:true,eligibleForAcquisition:false,eligibleForExecution:false,modelId:c.modelId,artifactSha256:c.artifactSha256,notice:"Metadata checks do not authorize download, installation, loading, or inference."});
}
function checklist(){return Object.freeze(["Confirm publisher identity and provenance independently.","Read exact license version and assess intended use.","Review model card, training/data disclosures, and restrictions.","Review artifact format, checksum, and supply-chain risks.","Complete security review before any acquisition proposal.","Obtain explicit user approval for a separately scoped action."]);}
root.AIBridgeLocalAIModelGovernance=Object.freeze({validate:validate,createReviewChecklist:checklist});
})(typeof window!=="undefined"?window:globalThis);
