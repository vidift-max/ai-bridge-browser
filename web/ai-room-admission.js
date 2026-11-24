/* Multi-AI room admission; host-side authorization contract only. */
(function(root){
 "use strict";
 var ROLES=Object.freeze(["COORDINATOR","PARTICIPANT","OBSERVER"]);
 function validId(v){return typeof v==="string"&&/^[A-Za-z0-9._:-]{1,128}$/.test(v);}
 function create(options){
  options=options||{};
  var sessions=options.sessions;
  var now=typeof options.now==="function"?options.now:Date.now;
  var max=Number.isInteger(options.maxParticipants)?options.maxParticipants:6;
  if(!sessions||typeof sessions.getSession!=="function")throw new Error("SESSION_REGISTRY_REQUIRED");
  if(max<2||max>32)throw new Error("ROOM_CAPACITY_INVALID");
  var rooms=new Map();
  function activeSession(id){
   var s=sessions.getSession(id);
   if(!s||s.state!=="CONNECTED")throw new Error("CONNECTED_SESSION_REQUIRED");
   if(!validId(s.sessionId)||s.sessionId!==id||!validId(s.providerId))throw new Error("SESSION_BINDING_INVALID");
   return s;
  }
  function participantView(p){
   return Object.freeze({aiId:p.aiId,sessionId:p.sessionId,providerId:p.providerId,role:p.role,
    status:p.status,admittedAt:p.admittedAt});
  }
  function roomFor(id){
   var r=rooms.get(id);
   if(!r||r.status!=="ACTIVE")throw new Error("ROOM_NOT_ACTIVE");
   return r;
  }
  function coordinator(r,aiId){
   var p=r.members.get(aiId);
   if(!p||p.status!=="ACTIVE"||p.role!=="COORDINATOR")throw new Error("COORDINATOR_REQUIRED");
   activeSession(p.sessionId);
   return p;
  }
  function createRoom(input){
   input=input||{};
   if(!validId(input.roomId)||!validId(input.coordinatorAiId)||!validId(input.coordinatorSessionId))
    throw new Error("ROOM_IDENTITY_INVALID");
   if(rooms.has(input.roomId))throw new Error("ROOM_ALREADY_EXISTS");
   var s=activeSession(input.coordinatorSessionId);
   var r={roomId:input.roomId,status:"ACTIVE",createdAt:now(),members:new Map(),invitations:new Map()};
   r.members.set(input.coordinatorAiId,{aiId:input.coordinatorAiId,sessionId:s.sessionId,
    providerId:s.providerId,role:"COORDINATOR",status:"ACTIVE",admittedAt:now()});
   rooms.set(r.roomId,r);
   return snapshot(r);
  }
  function issueInvitation(input){
   input=input||{};
   var r=roomFor(input.roomId);
   coordinator(r,input.issuedByAiId);
   if(!validId(input.invitationId)||!validId(input.aiId))throw new Error("INVITATION_IDENTITY_INVALID");
   if(!ROLES.includes(input.role)||input.role==="COORDINATOR")throw new Error("INVITATION_ROLE_INVALID");
   if(r.invitations.has(input.invitationId))throw new Error("INVITATION_ALREADY_EXISTS");
   if(r.members.has(input.aiId))throw new Error("AI_ALREADY_IN_ROOM");
   var expiry=input.expiresAt;
   if(!Number.isFinite(expiry)||expiry<=now()||expiry>now()+600000)throw new Error("INVITATION_EXPIRY_INVALID");
   var invitation={invitationId:input.invitationId,aiId:input.aiId,role:input.role,
    expiresAt:expiry,issuedByAiId:input.issuedByAiId,status:"PENDING"};
   r.invitations.set(invitation.invitationId,invitation);
   return Object.freeze({roomId:r.roomId,invitationId:invitation.invitationId,aiId:invitation.aiId,
    role:invitation.role,expiresAt:invitation.expiresAt});
  }
  function admit(input){
   input=input||{};
   var r=roomFor(input.roomId);
   var invitation=r.invitations.get(input.invitationId);
   if(!invitation||invitation.status!=="PENDING")throw new Error("INVITATION_NOT_AVAILABLE");
   if(now()>=invitation.expiresAt){invitation.status="EXPIRED";throw new Error("INVITATION_EXPIRED");}
   if(input.aiId!==invitation.aiId||!validId(input.sessionId))throw new Error("INVITATION_IDENTITY_MISMATCH");
   var activeCount=Array.from(r.members.values()).filter(function(member){return member.status==="ACTIVE";}).length;
   if(activeCount>=max)throw new Error("ROOM_CAPACITY_REACHED");
   if(r.members.has(input.aiId))throw new Error("AI_ALREADY_IN_ROOM");
   for(var member of r.members.values()){
    if(member.status==="ACTIVE"&&member.sessionId===input.sessionId)throw new Error("SESSION_ALREADY_IN_ROOM");
   }
   var s=activeSession(input.sessionId);
   var p={aiId:input.aiId,sessionId:s.sessionId,providerId:s.providerId,role:invitation.role,
    status:"ACTIVE",admittedAt:now()};
   invitation.status="CONSUMED";
   r.members.set(p.aiId,p);
   return participantView(p);
  }
  function revoke(input){
   input=input||{};
   var r=roomFor(input.roomId);
   coordinator(r,input.byAiId);
   var target=r.members.get(input.aiId);
   if(!target||target.status!=="ACTIVE")throw new Error("ROOM_MEMBER_NOT_FOUND");
   if(target.role==="COORDINATOR")throw new Error("COORDINATOR_CANNOT_BE_REVOKED");
   target.status="REVOKED";
   target.revokedAt=now();
   return participantView(target);
  }
  function leave(input){
   input=input||{};
   var r=roomFor(input.roomId);
   var target=r.members.get(input.aiId);
   if(!target||target.status!=="ACTIVE"||target.sessionId!==input.sessionId)throw new Error("ROOM_MEMBER_NOT_FOUND");
   if(target.role==="COORDINATOR")throw new Error("COORDINATOR_MUST_CLOSE_ROOM");
   target.status="LEFT";
   target.leftAt=now();
   return participantView(target);
  }
  function authorizeMessage(input){
   input=input||{};
   var r=roomFor(input.roomId);
   var p=r.members.get(input.aiId);
   if(!p||p.status!=="ACTIVE"||p.sessionId!==input.sessionId)throw new Error("ROOM_MEMBERSHIP_REQUIRED");
   activeSession(p.sessionId);
   if(p.role==="OBSERVER")throw new Error("ROOM_ROLE_READ_ONLY");
   return Object.freeze({roomId:r.roomId,aiId:p.aiId,sessionId:p.sessionId,authorized:true});
  }
  function snapshot(r){
   return Object.freeze({roomId:r.roomId,status:r.status,createdAt:r.createdAt,
    participants:Object.freeze(Array.from(r.members.values()).map(participantView))});
  }
  function getRoom(id){var r=rooms.get(id);return r?snapshot(r):null;}
  function closeRoom(input){
   input=input||{};
   var r=roomFor(input.roomId);
   coordinator(r,input.byAiId);
   r.status="CLOSED";
   r.closedAt=now();
   r.invitations.forEach(function(i){if(i.status==="PENDING")i.status="REVOKED";});
   r.members.forEach(function(p){p.status="ROOM_CLOSED";});
   return snapshot(r);
  }
  return Object.freeze({createRoom:createRoom,issueInvitation:issueInvitation,admit:admit,
   revoke:revoke,leave:leave,authorizeMessage:authorizeMessage,getRoom:getRoom,closeRoom:closeRoom});
 }
 root.AIBridgeRoomAdmission=Object.freeze({create:create,roles:ROLES});
})(typeof window!=="undefined"?window:globalThis);
