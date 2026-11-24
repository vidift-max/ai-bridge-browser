(function(root){
 "use strict";
 async function copyMessage(text,clipboard){
  if(typeof text!=="string"||!text.trim())throw new Error("ROOM_MESSAGE_TEXT_REQUIRED");
  if(!clipboard||typeof clipboard.writeText!=="function")throw new Error("CLIPBOARD_UNAVAILABLE");
  await clipboard.writeText(text);
  return true;
 }
 root.AIBridgeRoomMessageActions=Object.freeze({copyMessage});
})(typeof window!=="undefined"?window:globalThis);
