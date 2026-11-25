/* Composition root for the bounded loop and authenticated provider boundary.
 * The host supplies provider invocation, cryptographic attestation verification and UI rendering. */
(function(root){
 "use strict";
 function create(options){
  options=options||{};
  if(!root.AIBridgeAuthenticatedAgentAdapter||!root.AIBridgeConversationLoop)
   throw new Error("AI_CONVERSATION_RUNTIME_MODULES_REQUIRED");
  const adapter=root.AIBridgeAuthenticatedAgentAdapter.create(options);
  const controller=root.AIBridgeConversationLoop.create({
   getContext:options.getContext,
   respond:adapter.respond,
   deliver:adapter.deliver,
   onState:options.onState
  });
  return Object.freeze({
   start:config=>controller.start(config),
   stop:()=>controller.stop(),
   snapshot:()=>controller.snapshot(),
   subscribe:listener=>controller.subscribe(listener)
  });
 }
 root.AIBridgeConversationRuntime=Object.freeze({create});
})(typeof window!=="undefined"?window:globalThis);
