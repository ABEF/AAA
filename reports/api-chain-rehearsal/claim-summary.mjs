import {DeploymentAPI,ZERO} from 'file:///C:/Users/Ali/Desktop/2.x%20holas/Oto/aaa-website/deployment-api.js';
import {DeploymentSession} from 'file:///C:/Users/Ali/Desktop/2.x%20holas/Oto/aaa-website/deployment-session.js';
import {DeploymentTransactions} from 'file:///C:/Users/Ali/Desktop/2.x%20holas/Oto/aaa-website/deployment-transactions.js';
import {readFile,readdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const work=new URL('./',import.meta.url),run=(await readdir(new URL('runs/',work))).sort().at(-1);
const home=new URL(`runs/${run}/`,work),m=JSON.parse(await readFile(new URL('website-manifest.json',home))),r=JSON.parse(await readFile(new URL('running.json',home)));
const account=r.accounts[0],store=()=>{const s=new Map();return {getItem:k=>s.get(k)??null,setItem:(k,v)=>s.set(k,v),removeItem:k=>s.delete(k)}};
let unavailable=false,sends=0,seq=0;
const rpc=async(method,params=[])=>{const v=await(await fetch(m.rpc_url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:++seq,method,params})})).json();if(v.error)throw Error(v.error.message);return v.result;};
assert.equal(await rpc('eth_chainId'),'0x7a69');assert.equal((await rpc('eth_getBlockByNumber',['0x0',false])).hash,m.genesis_hash);
const api=new DeploymentAPI(m,{origin:r.url,fetcher:async(url,opt={})=>{
  if(unavailable&&url.endsWith('/v1/protocol'))throw Error('Intentional read outage after confirmed claim');
  return fetch(url,{...opt,headers:{...opt.headers,...(opt.method==='POST'?{Origin:r.url}:{})}});
}});
const provider={on(){},removeListener(){},async request({method,params=[]}){
  if(['eth_accounts','eth_requestAccounts'].includes(method))return[account];
  if(!['eth_chainId','eth_getBlockByNumber','eth_sendTransaction'].includes(method))throw Error('Unexpected method');
  if(method==='eth_sendTransaction'){assert.equal(params[0].from,account);sends++;const hash=await rpc(method,params);unavailable=true;return hash;}
  return rpc(method,params);
}};
const session=new DeploymentSession({key:'claim-real-api',storage:store()});await session.connect({provider,id:'local-probe',name:'Local RPC probe'});
const storage=store(),locks={request:async(k,o,f)=>f({name:k})};
const coordinator=()=>new DeploymentTransactions(api,session,{walletOptions:{storage,locks}});
const inv=await api.request(`/v1/wallets/${account}/nfts`);assert.equal(inv.count,18);
const before=await api.walletTotals(inv);assert.equal(before.count,18);assert.ok(BigInt(before.lp_usd_18)>15000n*10n**18n);assert.ok(BigInt(before.claimable_eth_wei)>0n);
let selected;
for(const id of inv.token_ids){const n=await api.nft(id,account);if(n.position.activated&&n.claimable.lp.some(a=>a.asset===ZERO&&BigInt(a.raw)>0n)){selected=n;break;}}
assert.ok(selected);let txs=coordinator();const review=await txs.prepare({action:'claim',ids:[selected.token_id]});
const amount=review.claims.reduce((s,c)=>s+BigInt(c.simulated_raw),0n),balanceBefore=BigInt(await rpc('eth_getBalance',[account,'latest']));
const result=await txs.submit(review);assert.equal(result.status,'confirmed');assert.equal(result.reconciled,false);assert.ok(txs.pending());
const saved=JSON.parse(JSON.stringify(txs.pending()));unavailable=false;txs=coordinator();
const recovered=await txs.recover();assert.equal(recovered.status,'confirmed');assert.equal(recovered.reconciled,true);assert.equal(txs.pending(),null);assert.equal(sends,1);
const afterNFT=await api.nft(selected.token_id,account);assert.equal(afterNFT.position.current_lp_value.raw,selected.position.current_lp_value.raw);
for(const part of ['lp','royalties'])assert.equal(afterNFT.claimable[part].find(a=>a.asset===ZERO).raw,'0');
const after=await api.walletTotals(await api.request(`/v1/wallets/${account}/nfts`));assert.equal(BigInt(before.claimable_eth_wei)-BigInt(after.claimable_eth_wei),amount);
const balanceAfter=BigInt(await rpc('eth_getBalance',[account,'latest'])),receipt=await rpc('eth_getTransactionReceipt',[recovered.hash]);
assert.equal(balanceAfter-balanceBefore,amount-BigInt(receipt.gasUsed)*BigInt(receipt.effectiveGasPrice));
await writeFile(new URL('claim-summary.json',work),JSON.stringify({run,account,before,after,selected:selected.token_id,review,result,recovered,saved,receipt,sends,balanceBefore:String(balanceBefore),balanceAfter:String(balanceAfter),amount:String(amount),passed:true,scope:'Actual local Anvil, real HTTP/API; deliberately injected API outage only. RPC shim, not extension acceptance.'},null,2));
console.log('PASS: 18 holdings across two summary chunks; actual combined ETH claim; API-outage/reload recovery; exactly one send; exact payout minus gas');
