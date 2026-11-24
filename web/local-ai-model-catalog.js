/* Mission 22: metadata-only local model reference catalog.
 * Entries are planning profiles, not downloadable model artifacts.
 * This module performs no network, storage, model loading, or inference.
 */
(function (root) {
  "use strict";
  var PROFILES = [
    { id:"reference-small-0.5b-q4", label:"Perfil pequeno — referência 0,5B / Q4", family:"GENERIC_INSTRUCT", parameterScale:"0.5B", quantization:"Q4", approximateArtifactSize:"PROFILE_ONLY", minimumMemoryBucket:"4_TO_7_GB", requiredApis:["webgpu.adapter","workers"], licenseStatus:"NOT_ASSESSED" },
    { id:"reference-medium-1.5b-q4", label:"Perfil médio — referência 1,5B / Q4", family:"GENERIC_INSTRUCT", parameterScale:"1.5B", quantization:"Q4", approximateArtifactSize:"PROFILE_ONLY", minimumMemoryBucket:"8_GB_OR_MORE", requiredApis:["webgpu.adapter","workers"], licenseStatus:"NOT_ASSESSED" },
    { id:"reference-large-3b-q4", label:"Perfil maior — referência 3B / Q4", family:"GENERIC_INSTRUCT", parameterScale:"3B", quantization:"Q4", approximateArtifactSize:"PROFILE_ONLY", minimumMemoryBucket:"8_GB_OR_MORE", requiredApis:["webgpu.adapter","workers"], licenseStatus:"NOT_ASSESSED" }
  ];
  var MEMORY_RANK = { UNKNOWN:0, UP_TO_3_GB:1, "4_TO_7_GB":2, "8_GB_OR_MORE":3 };
  function cloneProfile(p) {
    return Object.freeze({ id:p.id, label:p.label, family:p.family, parameterScale:p.parameterScale, quantization:p.quantization, approximateArtifactSize:"PROFILE_ONLY", minimumMemoryBucket:p.minimumMemoryBucket, requiredApis:Object.freeze(p.requiredApis.slice()), artifactAvailable:false, downloadUrl:null, licenseStatus:p.licenseStatus, compatibility:"UNVERIFIED", catalogType:"REFERENCE_PROFILE" });
  }
  function listProfiles() { return Object.freeze(PROFILES.map(cloneProfile)); }
  function findProfile(id) { var p=PROFILES.find(function(x){return x.id===id;}); return p?cloneProfile(p):null; }
  function evaluate(profileOrId, report) {
    var p=typeof profileOrId==="string"?findProfile(profileOrId):profileOrId;
    if(!p) return Object.freeze({status:"UNKNOWN_PROFILE",eligibleForReview:false,reasons:["UNKNOWN_PROFILE"]});
    var reasons=[];
    if(!report||report.schemaVersion!==1||report.runtimeScope!=="user_device_browser") reasons.push("CAPABILITY_REPORT_MISSING_OR_UNSUPPORTED");
    else {
      if(report.status!=="LOCAL_AI_CANDIDATE_READY") reasons.push("DEVICE_CAPABILITY_NOT_READY");
      if(report.secureContext!==true) reasons.push("SECURE_CONTEXT_REQUIRED");
      if(!report.network||report.network.allowed!==true) reasons.push("WIFI_POLICY_NOT_CONFIRMED");
      if(!report.apis||!report.apis.webgpu||report.apis.webgpu.adapterAvailable!==true) reasons.push("WEBGPU_ADAPTER_REQUIRED");
      if(!report.apis||report.apis.workers!==true) reasons.push("WORKERS_REQUIRED");
      var memory=report.resourceHints&&report.resourceHints.memoryBucket;
      if(!Object.prototype.hasOwnProperty.call(MEMORY_RANK,memory)) reasons.push("MEMORY_HINT_UNKNOWN");
      else if(MEMORY_RANK[memory]<MEMORY_RANK[p.minimumMemoryBucket]) reasons.push("MEMORY_HINT_BELOW_PROFILE_THRESHOLD");
      if(!report.execution||report.execution.modelLoaded!==false||report.execution.downloadStarted!==false||report.execution.inferenceStarted!==false) reasons.push("EXECUTION_STATE_NOT_INERT");
    }
    var eligible=reasons.length===0;
    return Object.freeze({profileId:p.id,status:eligible?"POTENTIAL_CANDIDATE_REQUIRES_BENCHMARK":"NOT_RECOMMENDED",eligibleForReview:eligible,reasons:Object.freeze(reasons),caveat:"Heuristic only: no artifact, memory fit, driver compatibility, benchmark, or inference has been verified."});
  }
  function recommend(report) {
    return Object.freeze(listProfiles().map(function(p){return Object.freeze({profile:p,assessment:evaluate(p,report)});}).sort(function(a,b){
      if(a.assessment.eligibleForReview!==b.assessment.eligibleForReview) return a.assessment.eligibleForReview?-1:1;
      return MEMORY_RANK[a.profile.minimumMemoryBucket]-MEMORY_RANK[b.profile.minimumMemoryBucket];
    }));
  }
  root.AIBridgeLocalAIModelCatalog=Object.freeze({listProfiles:listProfiles,findProfile:findProfile,evaluate:evaluate,recommend:recommend});
})(typeof window!=="undefined"?window:globalThis);
