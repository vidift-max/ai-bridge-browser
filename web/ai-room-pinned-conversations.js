(function(root){
 "use strict";
 const KEY="aiBridgePinnedConversations.v1";
 function validId(value){return typeof value==="string"&&value.trim().length>0&&value.length<=200}
 function createStore(storage){
  if(!storage)throw new Error("pinned_conversation_storage_required");
  function read(){
   const raw=storage.getItem(KEY);
   if(raw===null)return [];
   let parsed;try{parsed=JSON.parse(raw)}catch{return []}
   if(!Array.isArray(parsed))return [];
   return [...new Set(parsed.filter(validId))];
  }
  function write(ids){storage.setItem(KEY,JSON.stringify([...new Set(ids.filter(validId))]));}
  function list(){return read()}
  function has(id){return validId(id)&&read().includes(id)}
  function toggle(id){
   if(!validId(id))throw new Error("invalid_conversation_id");
   const ids=read(),index=ids.indexOf(id);
   if(index>=0){ids.splice(index,1);write(ids);return false}
   ids.unshift(id);write(ids);return true;
  }
  function sort(rooms){
   if(!Array.isArray(rooms))throw new Error("invalid_conversation_list");
   const pinned=new Set(read());
   return rooms.map((room,index)=>({room,index})).sort((a,b)=>{
    const ap=pinned.has(a.room?.conversationId)?1:0,bp=pinned.has(b.room?.conversationId)?1:0;
    return bp-ap||a.index-b.index;
   }).map(item=>item.room);
  }
  return {list,has,toggle,sort};
 }
 root.AIBridgePinnedConversations={createStore,KEY};
})(typeof window!=="undefined"?window:globalThis);
