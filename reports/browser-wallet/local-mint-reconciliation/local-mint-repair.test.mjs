import {test} from 'node:test';
import assert from 'node:assert/strict';
import {archiveAuthorizedLocalMint as repair} from './local-mint-repair.mjs';
const owner='0x70997970c51812dc3a010c7d01b50e0d17dc79c8',hash='0x7df63aa0d6bf24461b7fdf1858b778c7d1e051d904a11a86ad0dd538a9400cc6',genesis='0x19df3ff29a52f43ea4c9120bcbf65ec6a3d707f90c4e6537d54274cfe3f4d439',key=`popl-browser-pending-v1:0x7a69:${genesis}:${owner}`;
function fixture(){
 const item={schema:1,status:'pending',hash,genesisHash:genesis,transaction:{from:owner,to:'0x2279b7a0a67db372996a5fab50d91eaa73d2ebe6',chainId:'0x7a69',data:'0x21bf772d',value:'0xb1a2bc2ec50000',nonce:'0x19'}};
 const values=new Map([[key,JSON.stringify(item)],['other-account','preserve']]);let deletes=0;
 const storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>{deletes++;values.delete(k);}};
 const args={origin:'http://127.0.0.1:8902',config:{environment:'rehearsal',chain_id:31337,genesis_hash:genesis,rpc_url:'http://127.0.0.1:57306'},nonceHistoryCleared:true,storage,locks:{request:async(_k,_opts,f)=>f({})},rpc:async method=>({eth_chainId:'0x7a69',eth_getBlockByNumber:{hash:genesis},eth_getTransactionByHash:null,eth_getTransactionReceipt:null,eth_getTransactionCount:'0x19'})[method]};
 return {args,values,item,get deletes(){return deletes;}};
}
test('archive exact abandoned mint, retain byte-exact journal and every other key',async()=>{const s=fixture(),original=s.values.get(key),result=await repair(s.args);assert(result.archived);assert.equal(s.deletes,1);assert.equal(JSON.parse(s.values.get(result.archiveKey)).rawJournal,original);assert.equal(s.values.get('other-account'),'preserve');assert((await repair(s.args)).alreadyAbsent);assert.equal(s.deletes,1);});
const bad={
 'public origin':s=>s.args.origin='https://popldemo.0xwave.com',
 'wrong deployment':s=>s.args.config.chain_id=1,
 'unchecked MetaMask step':s=>s.args.nonceHistoryCleared=false,
 'different saved hash':s=>{s.item.hash='0x'+'1'.repeat(64);s.values.set(key,JSON.stringify(s.item));},
 'different mint nonce':s=>{s.item.transaction.nonce='0x20';s.values.set(key,JSON.stringify(s.item));},
 'mined receipt':s=>{const rpc=s.args.rpc;s.args.rpc=async(m,p)=>m==='eth_getTransactionReceipt'?{status:'0x1'}:rpc(m,p);},
 'rebroadcast transaction':s=>{const rpc=s.args.rpc;s.args.rpc=async(m,p)=>m==='eth_getTransactionByHash'?{hash}:rpc(m,p);},
 'changed account nonce':s=>{const rpc=s.args.rpc;s.args.rpc=async(m,p)=>m==='eth_getTransactionCount'?'0x1a':rpc(m,p);},
 'wrong genesis':s=>{const rpc=s.args.rpc;s.args.rpc=async(m,p)=>m==='eth_getBlockByNumber'?{hash:'0x0'}:rpc(m,p);},
 'busy other tab':s=>s.args.locks.request=async(_k,_o,f)=>f(null),
 'archive cannot persist':s=>s.args.storage.setItem=()=>{throw Error('storage full');},
 'journal changed during reads':s=>{const rpc=s.args.rpc;let n=0;s.args.rpc=async(m,p)=>{if(++n===8)s.values.set(key,'changed');return rpc(m,p);};}
};
for(const [name,mutate] of Object.entries(bad))test(name+' preserves pending record',async()=>{const s=fixture();mutate(s);await assert.rejects(repair(s.args));assert.equal(s.deletes,0);assert(s.values.has(key));assert.equal(s.values.get('other-account'),'preserve');});
