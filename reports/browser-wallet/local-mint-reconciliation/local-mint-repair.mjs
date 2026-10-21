// ONE-TIME LOCAL FIXTURE REPAIR. Never part of the public build or shared signer.
const REPAIR_OWNER='0x70997970c51812dc3a010c7d01b50e0d17dc79c8';
const REPAIR_HASH='0x7df63aa0d6bf24461b7fdf1858b778c7d1e051d904a11a86ad0dd538a9400cc6';
const REPAIR_GENESIS='0x19df3ff29a52f43ea4c9120bcbf65ec6a3d707f90c4e6537d54274cfe3f4d439';
const REPAIR_RPC='http://127.0.0.1:57306';
const REPAIR_KEY=`popl-browser-pending-v1:0x7a69:${REPAIR_GENESIS}:${REPAIR_OWNER}`;
export async function archiveAuthorizedLocalMint({origin,config,storage,locks,rpc,nonceHistoryCleared}){
  if(origin!=='http://127.0.0.1:8902'||config?.environment!=='rehearsal'||config.chain_id!==31337||config.genesis_hash!==REPAIR_GENESIS||config.rpc_url!==REPAIR_RPC)throw Error('This repair belongs only to the original local fixture.');
  if(nonceHistoryCleared!==true)throw Error('First clear MetaMask activity and nonce data on the local network.');
  return locks.request(REPAIR_KEY,{mode:'exclusive',ifAvailable:true},async lock=>{
    if(!lock)throw Error('Another tab is using this wallet. Close its operation first.');
    const saved=storage.getItem(REPAIR_KEY);
    if(saved===null)return {alreadyAbsent:true};
    if(saved.length>40000)throw Error('Unexpected recovery record size.');
    const item=JSON.parse(saved),tx=item?.transaction;
    if(item.schema!==1||item.status!=='pending'||item.hash!==REPAIR_HASH||item.genesisHash!==REPAIR_GENESIS||tx?.from!==REPAIR_OWNER||tx.to!=='0x2279b7a0a67db372996a5fab50d91eaa73d2ebe6'||tx.chainId!=='0x7a69'||tx.data!=='0x21bf772d'||tx.value!=='0xb1a2bc2ec50000'||!['0x19','0x23'].includes(tx.nonce))throw Error('Saved operation differs from the exact authorized mint. Nothing changed.');
    async function verify(){
      const [chain,genesis,transaction,receipt,latest,pending]=await Promise.all([
        rpc('eth_chainId',[]),rpc('eth_getBlockByNumber',['0x0',false]),rpc('eth_getTransactionByHash',[REPAIR_HASH]),rpc('eth_getTransactionReceipt',[REPAIR_HASH]),rpc('eth_getTransactionCount',[REPAIR_OWNER,'latest']),rpc('eth_getTransactionCount',[REPAIR_OWNER,'pending'])]);
      if(chain!=='0x7a69'||genesis?.hash!==REPAIR_GENESIS||transaction!==null||receipt!==null||latest!=='0x19'||pending!=='0x19')throw Error('The chain or queue changed. Stop and inspect; no record was removed.');
    }
    await verify();
    const archiveKey=`popl-local-abandoned-archive-v1:${REPAIR_GENESIS}:${REPAIR_HASH}`;
    const archive=JSON.stringify({scope:'User-authorized abandoned local mint. Not confirmed, not a chain cancellation; never rebroadcast the old signed transaction.',hash:REPAIR_HASH,rawJournal:saved});
    const previous=storage.getItem(archiveKey);
    if(previous!==null&&previous!==archive)throw Error('Different archive exists; preserve both records for inspection.');
    storage.setItem(archiveKey,archive);
    if(storage.getItem(archiveKey)!==archive)throw Error('Archive verification failed. Pending record preserved.');
    await verify();
    if(storage.getItem(REPAIR_KEY)!==saved)throw Error('Saved operation changed. Nothing removed.');
    storage.removeItem(REPAIR_KEY);
    if(storage.getItem(REPAIR_KEY)!==null)throw Error('Pending record could not be released. Archive retained.');
    return {archived:true,archiveKey};
  });
}

async function offerAuthorizedLocalMintRepair(){
  if(globalThis.location?.origin!=='http://127.0.0.1:8902')return;
  const {DEPLOYMENT:config}=await import('./deployment-config.js');
  if(config?.genesis_hash!==REPAIR_GENESIS||config.rpc_url!==REPAIR_RPC)return;
  let saved;try{saved=JSON.parse(localStorage.getItem(REPAIR_KEY));}catch{return;}
  if(saved?.hash!==REPAIR_HASH||document.getElementById('authorized-local-mint-repair'))return;
  const frame=document.createElement('section');frame.id='authorized-local-mint-repair';frame.className='container local-status';
  frame.innerHTML='<div><strong>Finish the approved local mint recovery</strong><p>The unmined mint was removed from this local node. Your NFTs and LP are unchanged.</p><p>In MetaMask, select Wallet A and the PoPL local network, then Settings → Developer tools → Delete activity and nonce data.</p><label><input type="checkbox" data-repair-ready> I cleared MetaMask’s activity and nonce data for this local network.</label><p><button type="button" class="button button-secondary" data-repair-go>Archive the abandoned mint and reconnect</button></p><p role="status" data-repair-status>This only archives the one approved local attempt. It never sends a transaction.</p></div>';
  document.querySelector('main').before(frame);
  let id=0;const rpc=async(method,params)=>{
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),5000);const requestId=++id;
    try{const response=await fetch(REPAIR_RPC,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:requestId,method,params}),signal:controller.signal,cache:'no-store'});
      if(!response.ok)throw Error('Local RPC unavailable.');const value=await response.json();if(value.error||value.id!==requestId||value.jsonrpc!=='2.0')throw Error('Local RPC response invalid.');return value.result;
    }finally{clearTimeout(timer);}
  };
  frame.querySelector('[data-repair-go]').addEventListener('click',async event=>{
    const button=event.currentTarget;button.disabled=true;
    try{const result=await archiveAuthorizedLocalMint({origin:location.origin,config,storage:localStorage,locks:navigator.locks,rpc,nonceHistoryCleared:frame.querySelector('[data-repair-ready]').checked});
      if(result.archived||result.alreadyAbsent){frame.querySelector('[data-repair-status]').textContent='Archived. Reloading confirmed balances; no transaction sent.';location.reload();}
    }catch(error){frame.querySelector('[data-repair-status]').textContent=error.message;button.disabled=false;}
  });
}
if(typeof document!=='undefined')void offerAuthorizedLocalMintRepair().catch(()=>{});
