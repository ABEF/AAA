import {DeploymentAPI} from 'file:///C:/Users/Ali/Desktop/2.x%20holas/Oto/aaa-website/deployment-api.js';
import {DeploymentSession} from 'file:///C:/Users/Ali/Desktop/2.x%20holas/Oto/aaa-website/deployment-session.js';
import {DeploymentTransactions} from 'file:///C:/Users/Ali/Desktop/2.x%20holas/Oto/aaa-website/deployment-transactions.js';
import {writeFile,readFile,readdir} from 'node:fs/promises';
import assert from 'node:assert/strict';
const work=new URL('./',import.meta.url),run=(await readdir(new URL('./runs/',work))).sort().at(-1);
const running=JSON.parse(await readFile(new URL(`runs/${run}/running.json`,work)));
const manifest=JSON.parse(await readFile(new URL(`runs/${run}/website-manifest.json`,work)));
const origin=running.url,account=running.accounts[1];
assert.equal(manifest.chain_id,31337);assert.match(manifest.rpc_url,/^http:\/\/127\.0\.0\.1:[0-9]+$/);
const store=()=>{const m=new Map();return {getItem:k=>m.get(k)??null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k)}};
let seq=0;
async function rpc(method,params=[]){const r=await fetch(manifest.rpc_url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:++seq,method,params})});const j=await r.json();if(j.error)throw Object.assign(Error(j.error.message),{code:j.error.code});return j.result;}
const provider={on(){},removeListener(){},async request({method,params=[]}){
  if(['eth_accounts','eth_requestAccounts'].includes(method))return [account];
  if(!['eth_chainId','eth_getBlockByNumber','eth_sendTransaction'].includes(method))throw Error('Unsupported local wallet probe method '+method);
  if(method==='eth_sendTransaction')assert.equal(params[0].from,account);
  return rpc(method,params);
}};
const api=new DeploymentAPI(manifest,{origin,fetcher:(url,opt={})=>fetch(url,{...opt,headers:{...opt.headers,...(opt.method==='POST'?{Origin:origin}:{})}})});
const session=new DeploymentSession({key:'local-api-journey',storage:store()});
await session.connect({provider,id:'local-anvil-probe',name:'Explicit local RPC test provider'});
const storage=store(),locks={request:async(key,options,fn)=>fn({name:key})};
const txs=new DeploymentTransactions(api,session,{walletOptions:{storage,locks},onProgress:v=>console.log('stage',v)});
const evidence={scope:'Actual Anvil + production unsigned APIs + shared local-only signer; RPC provider shim, NOT actual extension acceptance',run,started:new Date().toISOString(),journey:[]};
const save=()=>writeFile(new URL('journey.json',work),JSON.stringify(evidence,null,2));
async function action(intent,opts={}){
  console.log('prepare',intent.action,intent.asset||'');
  const review=await txs.prepare(intent,opts);
  const before=await rpc('eth_getBalance',[account,'latest']);
  const result=await txs.submit(review);
  evidence.journey.push({intent,review,result,balanceBefore:before,balanceAfter:await rpc('eth_getBalance',[account,'latest'])});await save();
  assert.equal(result.status,'confirmed');
  if(!result.reconciled){for(let n=0;n<6&&txs.pending();n++){await new Promise(r=>setTimeout(r,1000));await txs.recover();}}
  assert.equal(txs.pending(),null,'Confirmed operation must reconcile');
  return review;
}
try{
  await api.protocol();
  const initial=await api.request('/v1/wallets/'+account+'/nfts');
  await action({action:'mint'});
  let id;
  for(let n=0;n<15;n++){const inv=await api.request('/v1/wallets/'+account+'/nfts');id=inv.token_ids.find(id=>!initial.token_ids.includes(id));if(id&&(await api.nft(id,account)).traits_ready)break;await new Promise(r=>setTimeout(r,1000));}
  assert.ok(id,'minted NFT must be indexed and revealed');
  const amount=await api.activationAmount('ETH');assert.equal(amount.amount,'100');
  await action({action:'activate',id,asset:'ETH',amount:amount.amount});
  const activated=await api.nft(id,account);assert.equal(activated.position.activated,true);
  assert.ok(BigInt(activated.position.current_lp_value.raw)>=99n*10n**18n);
  assert.equal(activated.claimable.lp.find(a=>a.asset==='0x'+'0'.repeat(40)).raw,'0','No older LP rewards');
  const intent={action:'increase',id,asset:'USDC',amount:'5'};
  const approval=await action(intent);assert.equal(approval.action,'approve');
  assert.equal((await api.nft(id,account)).position.current_lp_value.raw,activated.position.current_lp_value.raw);
  const execution=await action(intent,{afterApproval:true});assert.equal(execution.action,'increase');
  const grown=await api.nft(id,account);assert.ok(BigInt(grown.position.current_lp_value.raw)>=BigInt(activated.position.current_lp_value.raw)+495n*10n**16n);
  evidence.newNft=id;evidence.grown=grown;
  evidence.completed=new Date().toISOString();await save();console.log('PASS',evidence.journey.length,'actual holder transactions');
}catch(error){evidence.failure={message:error.message,stack:error.stack};await save();throw error;}
