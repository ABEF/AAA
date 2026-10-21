import {BrowserWallet,createChainReader} from 'file:///C:/Users/Ali/Desktop/2.x%20holas/Oto/aaa-website/browser-wallet.js';
import {readFile,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const root=new URL('../runs/run-20261022-001857-b830df/',import.meta.url),m=JSON.parse(await readFile(new URL('website-manifest.json',root)));
const hash='0x7df63aa0d6bf24461b7fdf1858b778c7d1e051d904a11a86ad0dd538a9400cc6',reader=createChainReader(m.rpc_url),records=[];
const tx=await reader.request({method:'eth_getTransactionByHash',params:[hash]});
assert.equal(await reader.request({method:'eth_getTransactionReceipt',params:[hash]}),null);
const hex=n=>'0x'+BigInt(n).toString(16);
for(const nonce of [tx.nonce,'0x19']){
 const values=new Map(),storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};
 const wallet=new BrowserWallet({provider:{request:()=>{throw Error('No wallet access in read-only replay');}},readProvider:reader,storage,locks:{request:async(_k,_o,f)=>f({})},
   policy:{chainId:'0x7a69',genesisHash:m.genesis_hash,confirmations:m.confirmations,allowedTargets:Object.fromEntries(Object.values(m.contracts).map(c=>[c.address,c.runtime_code])),maxGas:hex(m.limits.gas),maxGasPrice:hex(m.limits.gas_price_wei),maxNetworkFee:hex(m.limits.network_fee_wei),maxValue:hex(m.limits.native_value_wei)}});
 const transaction=Object.fromEntries(['from','to','value','chainId','gas','gasPrice'].map(k=>[k,tx[k]]));transaction.data=tx.input;transaction.nonce=nonce;
 wallet.save({schema:1,id:'readonly-replay-observed-0001',genesisHash:m.genesis_hash,status:'pending',createdAt:Date.now(),transaction,context:{},hash,receipt:null});
 for(let i=0;i<3;i++){
   const start=performance.now(),result=await wallet.recover({account:tx.from});
   assert.equal(result.reason,nonce===tx.nonce?'nonce_gap':'review_nonce_changed');assert.equal(wallet.getPending(tx.from).hash,hash);
   records.push({reconstructed_review_nonce:nonce,elapsed_ms:Math.round(performance.now()-start),result});
 }
 wallet.close();
}
assert.equal(await reader.request({method:'eth_getTransactionReceipt',params:[hash]}),null);
assert.equal(await reader.request({method:'eth_getTransactionCount',params:[tx.from,'latest']}),'0x19');
await writeFile(new URL('replay.json',import.meta.url),JSON.stringify({scope:'Actual node reads only; isolated in-memory reconstructed reviews at signed nonce 35 and current nonce 25. The user browser journal was not accessed or altered. No wallet requests, sends, drops or state resets.',hash,records},null,2)+'\n');
console.log(JSON.stringify({passed:true,reads:records.length,max_ms:Math.max(...records.map(r=>r.elapsed_ms)),transaction_still_pending:true}));
