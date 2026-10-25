import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {setup} from './deployment-api.test.mjs';
import {DeploymentAPI} from '../deployment-api.js';
import {earnedUSD} from '../deployment-view.js';
const fixtures=JSON.parse(await readFile(new URL('./fixtures/earnings.json',import.meta.url)));
const digest=async ids=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(ids.join(','))))].map(n=>n.toString(16).padStart(2,'0')).join('');
function fixture(count=33,mutate=()=>{}){
  const s=setup();s.m.reward_assets=fixtures.wallet.all_time.map(r=>({address:r.asset,symbol:r.symbol,decimals:r.decimals}));s.api=new DeploymentAPI(s.m,{origin:'http://127.0.0.1:4188',reader:s.reader,clock:()=>s.now});s.inventory.token_ids=Array.from({length:count},(_,i)=>String(i+1));s.inventory.count=count;
  s.api.request=async path=>{
    const collection=path==='/v1/earnings',offset=collection?0:Number(path.split('/').at(-1));
    const part=structuredClone(fixtures[collection?'collection':'wallet']);part.provenance={...part.provenance,...s.inventory.provenance};
    part.window={after_timestamp_exclusive:Math.max(-1,part.provenance.block_timestamp-86400),through_timestamp_inclusive:part.provenance.block_timestamp};
    if(!collection){const ids=s.inventory.token_ids.slice(offset,offset+16);Object.assign(part,{wallet:s.inventory.wallet,nft_contract:s.m.contracts.nft.address,count,offset,token_ids:ids,inventory_sha256:await digest(s.inventory.token_ids),next_offset:offset+ids.length<count?offset+ids.length:null});}
    mutate(part,offset,s);return part;
  };return s;
}
test('actual Python collection and wallet responses validate without invented USD',async()=>{
  const s=fixture(1),out=await s.api.walletEarnings(s.inventory),c=await s.api.collectionEarnings();
  assert.equal(out.scope,'wallet');assert.equal(out.all_time[1].lp_individual_raw,'80');assert.equal(earnedUSD(out,'all_time'),null);
  assert.equal(c.scope,'collection');assert.equal(earnedUSD(c,'all_time',true),null);
});
test('all pages aggregate exact currencies before current-price valuation',async()=>{
  const s=fixture(),out=await s.api.walletEarnings(s.inventory);assert.equal(out.token_ids.length,33);assert.equal(out.all_time[1].lp_individual_raw,'240');assert.equal(out.all_time[0].royalties_raw,'300');
});
for(const [name,change] of [
  ['wrong owner',p=>p.wallet='0x'+'7'.repeat(40)],['different block',p=>p.provenance.block_hash='0x'+'9'.repeat(64)],
  ['missing currency',p=>p.all_time.pop()],['duplicate currency',p=>p.all_time[1]=p.all_time[0]],
  ['invented USD',p=>p.all_time_usd_at_current_price_18.royalties='100'],
  ['negative earnings',p=>p.all_time[0].royalties_raw='-1'],['claims as income',p=>p.claims_and_conversions_are_income=true],
  ['missing chunk',p=>p.next_offset=null],['changed inventory',p=>p.inventory_sha256='0'.repeat(64)],
  ['wrong IDs',p=>p.token_ids=['999']],['wrong window',p=>p.window.through_timestamp_inclusive++],
  ['day exceeds lifetime',p=>p.last_24h[0].royalties_raw='999'],
])test(name+' rejects entire earnings total',async()=>{const s=fixture(33,(p,n)=>{if(n===16)change(p)});await assert.rejects(s.api.walletEarnings(s.inventory));});
test('cancel or missing middle response never returns a partial wallet total',async()=>{
  const controller=new AbortController(),s=fixture(33,(p,n)=>{if(n===16)controller.abort();});await assert.rejects(s.api.walletEarnings(s.inventory,{signal:controller.signal}));
  const unavailable=fixture(33,(p,n)=>{if(n===16)throw Error('503');});await assert.rejects(unavailable.api.walletEarnings(unavailable.inventory));
});
test('production mint preparation rejected before network calls',async()=>{
  const s=setup('mint');const m={...s.m,environment:'production',chain_id:46630,rpc_url:'https://rpc.example.org'};
  const api=new DeploymentAPI(m,{origin:'https://example.org',fetcher:()=>assert.fail('No mint API request'),reader:{request:()=>assert.fail('No RPC request')}});
  await assert.rejects(api.prepare(s.intent),/OpenSea/);
});
test('collection holder allocations exclude compound buyback quarantine and gross duplicate',()=>{
  const r={available:true,all_time_usd_at_current_price_18:{lp_processed:'1000',lp_owner_allocated:'800',lp_collective_allocated:'100',royalties_allocated:'20',lp_compounding_allocated:'50',lp_buyback_allocated:'50',royalties_quarantined:'900'}};
  assert.equal(earnedUSD(r,'all_time',true),'920');
});

test('empty holdings reject invented positive history and verify zero without prices',async()=>{
  const bad=fixture(0);await assert.rejects(bad.api.walletEarnings(bad.inventory),/Empty holdings/);
  const good=fixture(0,p=>{for(const period of ['all_time','last_24h']){for(const row of p[period])for(const k of ['lp_individual','lp_collective','royalties']){row[k+'_raw']='0';row.usd_at_current_price_18[k]='0';}p[period+'_usd_at_current_price_18']={lp_individual:'0',lp_collective:'0',royalties:'0'};}});
  assert.equal(earnedUSD(await good.api.walletEarnings(good.inventory),'all_time'),'0');
});
test('1000 holdings use exactly 63 bounded earnings requests',async()=>{let calls=0;const s=fixture(1000,()=>calls++);const result=await s.api.walletEarnings(s.inventory);assert.equal(calls,63);assert.equal(result.token_ids.length,1000);});