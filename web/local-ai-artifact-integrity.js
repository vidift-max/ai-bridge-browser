(function(root) {
"use strict";
var HEX=/^[a-f0-9]{64}$/;
var ID=/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
var FORMATS=["GGUF","ONNX","SAFETENSORS"];
var DEFAULT_MAX=2147483648;
function blocked(reasons){return Object.freeze({status:"BLOCKED",integrityVerified:false,eligibleForAcquisition:false,eligibleForExecution:false,reasons:Object.freeze(reasons)});}
function validateManifest(m, governance, options){
var r=[], max=options&&Number.isSafeInteger(options.maxBytes)&&options.maxBytes>0?options.maxBytes:DEFAULT_MAX;
if(!m||typeof m!=="object"||Array.isArray(m))return blocked(["MANIFEST_REQUIRED"]);
if(m.schemaVersion!==1)r.push("UNSUPPORTED_SCHEMA");
if(typeof m.modelId!=="string"||!ID.test(m.modelId))r.push("INVALID_MODEL_ID");
if(typeof m.version!=="string"||!ID.test(m.version))r.push("INVALID_VERSION");
if(typeof m.sha256!=="string"||!HEX.test(m.sha256))r.push("INVALID_SHA256");
if(!Number.isSafeInteger(m.byteLength)||m.byteLength<1||m.byteLength>max)r.push("ARTIFACT_SIZE_OUT_OF_POLICY");
if(!FORMATS.includes(m.format))r.push("UNSUPPORTED_ARTIFACT_FORMAT");
if(!governance||governance.status!=="METADATA_REVIEW_COMPLETE_PENDING_SEPARATE_ACTION"||governance.eligibleForAcquisition!==false||governance.eligibleForExecution!==false)r.push("GOVERNANCE_GATE_NOT_SATISFIED");
else {
if(m.modelId!==governance.modelId)r.push("MODEL_ID_MISMATCH");
if(m.sha256!==governance.artifactSha256)r.push("GOVERNANCE_CHECKSUM_MISMATCH");
}
if(m.downloadUrl!==undefined||m.sourceUrl!==undefined||m.installPath!==undefined)r.push("REMOTE_OR_INSTALL_LOCATION_FORBIDDEN");
if(m.acquisitionStarted===true||m.executionStarted===true)r.push("SIDE_EFFECT_STATE_FORBIDDEN");
if(r.length)return blocked(r);
return Object.freeze({status:"MANIFEST_VALID_PENDING_LOCAL_BYTES",integrityVerified:false,eligibleForAcquisition:false,eligibleForExecution:false,modelId:m.modelId,sha256:m.sha256,byteLength:m.byteLength,format:m.format,notice:"Manifest validation is metadata-only; it does not prove artifact bytes or authorize acquisition or execution."});
}
async function verifyBytes(m, governance, bytes, options){
var meta=validateManifest(m,governance,options);
if(meta.status==="BLOCKED")return meta;
if(!(bytes instanceof Uint8Array))return blocked(["ARTIFACT_BYTES_MUST_BE_UINT8ARRAY"]);
if(bytes.byteLength!==m.byteLength)return blocked(["ARTIFACT_LENGTH_MISMATCH"]);
var cryptoApi=root.crypto;
if(!cryptoApi||!cryptoApi.subtle||typeof cryptoApi.subtle.digest!=="function")return blocked(["WEBCRYPTO_SHA256_UNAVAILABLE"]);
try{
var digest=await cryptoApi.subtle.digest("SHA-256",bytes);
var actual=Array.from(new Uint8Array(digest)).map(function(x){return x.toString(16).padStart(2,"0");}).join("");
if(actual!==m.sha256)return blocked(["ARTIFACT_CHECKSUM_MISMATCH"]);
return Object.freeze({status:"LOCAL_BYTES_INTEGRITY_VERIFIED",integrityVerified:true,eligibleForAcquisition:false,eligibleForExecution:false,modelId:m.modelId,sha256:actual,byteLength:bytes.byteLength,notice:"Only the supplied in-memory bytes were hashed. No file was fetched, stored, installed, loaded, or executed."});
}catch(_){return blocked(["ARTIFACT_HASH_FAILED"]);}
}
root.AIBridgeArtifactIntegrity=Object.freeze({validateManifest:validateManifest,verifyBytes:verifyBytes});
})(typeof window!=="undefined"?window:globalThis);
