// NEW compact wallet/gate checks. No historical test module is imported.
// Workload wires, prices and advancing clocks below are explicitly synthetic;
// the final separate case uses the neutral current-source native/NFT fixture.
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {DeploymentAPI} from '../deployment-api.js';
import {WalletReadGate,sharedReadGate} from '../deployment-wallet-view.js';
import {FRESH_CANONICAL_SCHEMA} from '../deployment-source9.js';
import {source10APISetup} from './helpers/source10-api-fixture.mjs';

const address=n=>'0x'+BigInt(n).toString(16).padStart(40,'0');
const hash=n=>'0x'+BigInt(n).toString(16).padStart(64,'0');
const hex=n=>'0x'+BigInt(n).toString(16);
const copy=x=>structuredClone(x);
const digest=ids=>createHash('sha256').update(ids.join(','),'ascii').digest('hex');
const fields=['lp_individual','lp_collective','royalties'];
const OWNER=address(30),OTHER=address(31),TIME=100000,BLOCK=99;
const tick=()=>new Promise(resolve=>queueMicrotask(resolve));
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
const defaultAmount=(i,a,period,f)=>BigInt(i+1)*BigInt(a+1)*BigInt(f+1)*(period==='all_time'?11n:3n)*((1n<<60n)+1n);

function fixture({count=17,source=10,assetCount=3,mutate=()=>{},onFetch=()=>{},amount=defaultAmount,
  prices=()=>({available:true,usd_per_token_18:'3333333333333333333'})}={}){
  const assets=Array.from({length:assetCount},(_,i)=>({address:address(i===0?0:19+i),symbol:i===0?'ETH':i===1?'ZZZ':'CUR'+i,
    decimals:i===0||i===1?18:i===2?6:i%3===0?9:36}));
  const ids=Array.from({length:count},(_,i)=>((1n<<255n)+BigInt(i+1)).toString());
  const manifest={schema:source===10?5:4,source_profile:source,accounting_version:7,chain_id:31337,
    deployment_block:1,deployment_block_hash:hash(1),genesis_hash:hash(12),confirmations:2,max_age_seconds:120,
    api_prefix:'/api',projection_sha256:'a'.repeat(64),contracts:{nft:{address:address(2)}},reward_assets:assets};
  const anchor={block_number:BLOCK,block_hash:hash(BLOCK),block_timestamp:TIME,observed_head:BLOCK+1,confirmations:2,
    finality:'confirmation_depth_only',protocol_finalized:false,eip1898_require_canonical:true,
    configuration_sha256:manifest.projection_sha256,accounting_version:7};
  const lifecycle={state:'operating',new_economic_work_available_by_lifecycle:true,claims_available_by_lifecycle:true,
    transfers_available_by_lifecycle:true,predecessor_controller:null,lp_exit_started:false};
  const history={available:true,from_block:1,start_block_hash:hash(1),start_parent_hash:hash(2),through_block:BLOCK,
    block_hash:anchor.block_hash,indexer_next_block:BLOCK+2,scope:'NEW synthetic complete-ingestion fixture.'};
  const s={assets,ids,manifest,anchor,lifecycle,history,now:TIME*1000,requests:[],rpc:[],proofs:0,identities:0,
    currentHash:anchor.block_hash,currentHead:BLOCK+1,active:0,maximum:0};
  const api=Object.create(DeploymentAPI.prototype);s.api=api;
  Object.assign(api,{manifest,origin:'http://127.0.0.1:4190',clock:()=>s.now,revision:0,active:null});
  api.reader={async request({method,params=[]}){
    s.rpc.push({method,params});assert.doesNotMatch(method,/send|sign|nonce|trace|anvil/i);
    if(method==='eth_blockNumber')return hex(s.currentHead);
    if(method==='eth_getBlockByNumber'&&params[0]===hex(BLOCK))return {number:hex(BLOCK),hash:s.currentHash,timestamp:hex(TIME)};
    throw Error('Unexpected compact fixture RPC '+method);
  }};
  // Deliberate graph seam for pure-wire workloads, distinct from the real
  // constructor/native graph/NFT composition at the end of this file.
  api.native={async verify(block){s.proofs++;assert.deepEqual(block,{blockHash:anchor.block_hash,requireCanonical:true});}};
  api.identity=async()=>{s.identities++;};
  s.part=(offset,assetOffset)=>{
    const selected=ids.slice(offset,offset+16),next=offset+selected.length<count?offset+selected.length:null;
    const common={schema:1,chain_id:manifest.chain_id,wallet:OWNER,nft_contract:manifest.contracts.nft.address,
      inventory_sha256:digest(ids),count,offset,chunk_size:16,token_ids:selected,next_offset:next,
      lifecycle:copy(lifecycle),provenance:copy(anchor)};
    const rows=assets.slice(assetOffset,assetOffset+4),assetNext=assetOffset+rows.length<assets.length?assetOffset+rows.length:null;
    const slice={asset_offset:assetOffset,asset_count:assets.length,asset_chunk_size:4,
      asset_ids:assets.map(a=>a.address),selected_asset_ids:rows.map(a=>a.address),
      asset_inventory_sha256:digest(assets.map(a=>a.address)),next_asset_offset:assetNext};
    const earnings={...copy(common),available:true,scope:'wallet_chunk',claims_and_conversions_are_income:false,
      unprocessed_revenue_included:false,clock:'on-chain processing/allocation time',
      window:{through_timestamp_inclusive:TIME,after_timestamp_exclusive:TIME-86400},...copy(slice)};
    for(const period of ['all_time','last_24h']){
      earnings[period]=rows.map(asset=>{
        const a=assets.indexOf(asset),price=prices(a,period,offset);
        const amounts=fields.map((_,f)=>selected.reduce((sum,id)=>sum+amount(ids.indexOf(id),a,period,f),0n));
        const mark=n=>price.available?n*BigInt(price.usd_per_token_18)/10n**BigInt(asset.decimals):n===0n?0n:null;
        return {asset:asset.address,symbol:asset.symbol,decimals:asset.decimals,current_price:copy(price),
          ...Object.fromEntries(fields.map((f,i)=>[f+'_raw',amounts[i].toString()])),
          usd_at_current_price_18:Object.fromEntries(fields.map((f,i)=>[f,mark(amounts[i])===null?null:mark(amounts[i]).toString()]))};
      });
      earnings[period+'_usd_at_current_price_18']=Object.fromEntries(fields.map(f=>[f,
        earnings[period].some(r=>r.usd_at_current_price_18[f]===null)?null:
          earnings[period].reduce((sum,r)=>sum+BigInt(r.usd_at_current_price_18[f]),0n).toString()]));
    }
    return {...copy(common),kind:'fixed_block_wallet_view_page',available:true,verified_count:selected.length,
      complete:offset===0&&selected.length===count,history:copy(history),...slice,
      summary:assetOffset===0?{...copy(common),lp_usd_18:selected.reduce((sum,id)=>sum+(1n<<70n)+BigInt(ids.indexOf(id)),0n).toString(),
        claimable_eth_wei:selected.reduce((sum,id)=>sum+(1n<<65n)+BigInt(ids.indexOf(id)),0n).toString()}:null,
      earnings,earnings_error:null};
  };
  api.fetcher=async(url,options={})=>{
    const path=new URL(url).pathname.replace(/^\/api/,''),match=path.match(/^\/v1\/wallets\/(0x[0-9a-f]{40})\/view\/(\d+)\/(\d+)\/(\d+)$/);
    assert.ok(match,'Only compact read endpoints are permitted');assert.equal(match[1],OWNER);assert.equal(Number(match[2]),BLOCK);
    assert.equal(options.method,'GET');assert.equal(options.credentials,'omit');assert.equal(options.redirect,'error');
    const offset=Number(match[3]),assetOffset=Number(match[4]);s.requests.push({path,offset,assetOffset,signal:options.signal});
    const part=s.part(offset,assetOffset);s.active++;s.maximum=Math.max(s.maximum,s.active);
    try{await tick();await onFetch(offset,assetOffset,s,options);await mutate(part,offset,assetOffset,s);return new Response(JSON.stringify(part));}
    finally{s.active--;}
  };
  s.read=(options={})=>api.walletView(OWNER,copy(anchor),{lifecycle:copy(lifecycle),...options});
  s.expected=(period,a,f)=>{let result=0n;for(let i=0;i<count;i++)result+=amount(i,a,period,f);return result;};
  return s;
}

for(const source of [9,10])for(const count of [0,1,17,1000])test(`NEW compact source${source} ${count} holdings uses complete exact three-currency pages`,async()=>{
  const s=fixture({source,count}),out=await s.read(),index=BigInt(count)*BigInt(Math.max(0,count-1))/2n;
  assert.equal(out.inventory.complete,true);assert.deepEqual(out.inventory.token_ids,s.ids);assert.equal(out.inventory.inventory_sha256,digest(s.ids));
  assert.equal(out.totals.lp_usd_18,(BigInt(count)*(1n<<70n)+index).toString());
  assert.equal(out.totals.claimable_eth_wei,(BigInt(count)*(1n<<65n)+index).toString());
  assert.equal(out.earnings.scope,'wallet');assert.equal(out.earnings.token_ids.length,count);assert.equal(out.earnings_error,null);
  for(const period of ['all_time','last_24h'])for(const [a,row] of out.earnings[period].entries())for(const [f,field] of fields.entries()){
    const expected=s.expected(period,a,f);assert.equal(row[field+'_raw'],expected.toString());
    assert.equal(row.usd_at_current_price_18[field],(expected*3333333333333333333n/10n**BigInt(row.decimals)).toString());
  }
  assert.equal(s.requests.length,Math.max(1,Math.ceil(count/16)));assert.equal(s.maximum,1);assert.ok(s.proofs>=s.requests.length+2);
  assert.equal(s.identities,1);assert.equal(out.earnings.claims_and_conversions_are_income,false);
});

test('NEW compact sixteen NFTs and sixty-six descriptors complete all seventeen currency pages',async()=>{
  const s=fixture({count:16,assetCount:66}),out=await s.read();
  assert.equal(s.requests.length,17);assert.deepEqual(s.requests.map(r=>r.assetOffset),Array.from({length:17},(_,i)=>i*4));
  assert.equal(out.earnings.all_time.length,66);assert.deepEqual(out.earnings.all_time.map(r=>r.asset),s.assets.map(a=>a.address));
  for(const period of ['all_time','last_24h'])for(const [a,row] of out.earnings[period].entries())for(const [f,field] of fields.entries())
    assert.equal(row[field+'_raw'],s.expected(period,a,f).toString());
  assert.equal(out.inventory.count,16);assert.notEqual(out.totals.claimable_eth_wei,'0');
});

test('NEW compact maximum NFT-currency crossproduct preserves complete holdings and totals with unavailable earnings',async()=>{
  const s=fixture({count:1000,assetCount:66}),out=await s.read();
  assert.equal(s.requests.length,63);assert.ok(s.requests.every(r=>r.assetOffset===0));
  assert.deepEqual(out.inventory.token_ids,s.ids);assert.equal(out.inventory.complete,true);
  assert.equal(out.totals.lp_usd_18,(1000n*(1n<<70n)+499500n).toString());
  assert.equal(out.earnings,null);assert.match(out.earnings_error,/window/);
});

test('NEW compact aggregates raw amounts before the final per-asset USD floor',async()=>{
  const s=fixture({prices:()=>({available:true,usd_per_token_18:'1'}),amount:(_i,a,period,f)=>a===2&&f===2?(period==='all_time'?60000n:30000n):0n});
  assert.equal(s.part(0,0).earnings.all_time[2].usd_at_current_price_18.royalties,'0');
  assert.equal(s.part(16,0).earnings.all_time[2].usd_at_current_price_18.royalties,'0');
  const out=await s.read();assert.equal(out.earnings.all_time[2].royalties_raw,'1020000');assert.equal(out.earnings.all_time_usd_at_current_price_18.royalties,'1');
});

for(const metric of ['lp_usd_18','claimable_eth_wei'])test('NEW compact unavailable '+metric+' leaves the other complete metric and earnings available',async()=>{
  const s=fixture({mutate:(p,o,a)=>{if(o===16&&a===0)p.summary[metric]=null;}}),out=await s.read();
  assert.equal(out.totals[metric],null);assert.notEqual(out.totals[metric==='lp_usd_18'?'claimable_eth_wei':'lp_usd_18'],null);assert.ok(out.earnings);
});

test('NEW compact unpriced nonzero original currency keeps raw income and unavailable USD',async()=>{
  const s=fixture({prices:a=>a===2?{available:false,usd_per_token_18:null,reason:'synthetic missing feed'}:{available:true,usd_per_token_18:'1000000000000000000'}}),out=await s.read();
  assert.equal(out.earnings.all_time[2].royalties_raw,s.expected('all_time',2,2).toString());
  assert.equal(out.earnings.all_time_usd_at_current_price_18.royalties,null);assert.notEqual(out.totals.lp_usd_18,null);
});

test('NEW compact empty unpriced wallet remains authenticated exact zero',async()=>{
  const s=fixture({count:0,prices:()=>({available:false,usd_per_token_18:null,reason:'not configured'})}),out=await s.read();
  assert.equal(out.totals.lp_usd_18,'0');assert.equal(out.totals.claimable_eth_wei,'0');assert.equal(out.earnings.all_time_usd_at_current_price_18.royalties,'0');
});

const defects=[
  ['owner',p=>p.wallet=OTHER],['chain',p=>p.chain_id++],['NFT contract',p=>p.nft_contract=OTHER],
  ['inventory digest',p=>p.inventory_sha256='b'.repeat(64)],['NFT order',p=>p.token_ids.reverse()],
  ['count',p=>p.count++],['NFT cursor',p=>p.offset=0],['missing NFT suffix',p=>p.next_offset=null],
  ['verified count',p=>p.verified_count--],['false completion',p=>p.complete=true],
  ['block hash',p=>p.provenance.block_hash=hash(98)],['block timestamp',p=>p.provenance.block_timestamp--],
  ['configuration',p=>p.provenance.configuration_sha256='b'.repeat(64)],['canonical flag',p=>p.provenance.eip1898_require_canonical=false],
  ['accounting profile',p=>p.provenance.accounting_version=6],['history unavailable',p=>p.history.available=false],
  ['history suffix',p=>p.history.indexer_next_block=BLOCK],['history anchor',p=>p.history.start_parent_hash=hash(77)],
  ['lifecycle',p=>p.lifecycle.new_economic_work_available_by_lifecycle=false],
  ['currency cursor',p=>p.asset_offset=4],['asset digest',p=>p.asset_inventory_sha256='c'.repeat(64)],
  ['asset inventory',p=>p.asset_ids.pop()],['selected currencies',p=>p.selected_asset_ids.reverse()],
  ['missing currency suffix',p=>p.next_asset_offset=null],['asset count',p=>p.asset_count++],
  ['summary identity',p=>p.summary.wallet=OTHER],['summary token selection',p=>p.summary.token_ids=[]],
  ['earnings identity',p=>p.earnings.nft_contract=OTHER],['earnings snapshot',p=>p.earnings.provenance.block_timestamp--],
  ['nested earnings currency cursor',p=>p.earnings.asset_offset=4],['nested earnings currency digest',p=>p.earnings.asset_inventory_sha256='d'.repeat(64)],
  ['contradictory earnings error',p=>p.earnings_error='earnings_unavailable'],
  ['missing earnings currency',p=>p.earnings.all_time.pop()],['duplicate earnings currency',p=>p.earnings.all_time[1]=copy(p.earnings.all_time[0])],
  ['claims as income',p=>p.earnings.claims_and_conversions_are_income=true],['unprocessed income',p=>p.earnings.unprocessed_revenue_included=true],
  ['wrong day window',p=>p.earnings.window.after_timestamp_exclusive--],['invented USD total',p=>p.earnings.all_time_usd_at_current_price_18.royalties='1'],
  ['negative raw income',p=>p.earnings.all_time[0].royalties_raw='-1'],
];
for(const [label,change] of defects)test('NEW compact rejects '+label+' before publishing any partial result',async()=>{
  const s=fixture({count:33,assetCount:6,mutate:(p,o,a)=>{if(o===16&&a===0)change(p);}});
  await assert.rejects(s.read());
});

test('NEW compact rejects repeated summary on a later currency slice',async()=>{
  const s=fixture({count:16,assetCount:6,mutate:(p,o,a,s)=>{if(a===4)p.summary=s.part(o,0).summary;}});await assert.rejects(s.read(),/Repeated/);
});

test('NEW compact refuses a changed NFT selection between currency slices',async()=>{
  const s=fixture({count:16,assetCount:6,mutate:(p,_o,a)=>{if(a===4){p.token_ids=p.token_ids.map(id=>(BigInt(id)+100n).toString());p.earnings.token_ids=copy(p.token_ids);}}});
  await assert.rejects(s.read(),/selection changed/);
});

test('NEW compact final inventory digest authenticates even one apparently coherent page',async()=>{
  const s=fixture({count:1,mutate:p=>{p.inventory_sha256='c'.repeat(64);p.summary.inventory_sha256=p.inventory_sha256;p.earnings.inventory_sha256=p.inventory_sha256;}});
  await assert.rejects(s.read(),/inventory/);
});

test('NEW compact refuses locally valid prices changing across NFT pages',async()=>{
  const s=fixture({prices:(_a,_period,o)=>({available:true,usd_per_token_18:o===0?'1000000000000000000':'2000000000000000000'})});
  await assert.rejects(s.read(),/prices changed/);
});

for(const metric of ['lp_usd_18','claimable_eth_wei'])test('NEW compact empty positive '+metric+' is contradictory',async()=>{
  const s=fixture({count:0,mutate:p=>p.summary[metric]='1'});await assert.rejects(s.read(),/Empty wallet/);
});

test('NEW compact empty nonzero earnings is contradictory even when its local USD arithmetic is valid',async()=>{
  const s=fixture({count:0,amount:()=>0n,mutate:p=>{
    p.earnings.all_time[0].royalties_raw='1000000000000000000';
    p.earnings.all_time[0].usd_at_current_price_18.royalties='3333333333333333333';
    p.earnings.all_time_usd_at_current_price_18.royalties='3333333333333333333';
  }});await assert.rejects(s.read(),/Empty wallet/);
});

test('NEW compact bounded earnings refusal preserves all complete holdings and summary pages',async()=>{
  const s=fixture({mutate:(p,o)=>{if(o===16){p.earnings=null;p.earnings_error='earnings_unavailable';}}}),out=await s.read();
  assert.equal(out.inventory.count,17);assert.equal(out.inventory.complete,true);assert.notEqual(out.totals.lp_usd_18,null);
  assert.equal(out.earnings,null);assert.match(out.earnings_error,/unavailable/);assert.equal(s.requests.length,2);
});

test('NEW compact missing earnings requires the exact unavailable status',async()=>{
  const s=fixture({mutate:p=>{p.earnings=null;p.earnings_error=null;}});await assert.rejects(s.read(),/earnings status/);
});

for(const mode of ['abort','cancel'])test('NEW compact '+mode+' during the final HTTP response rejects late data',async()=>{
  const controller=new AbortController(),s=fixture({count:1,onFetch:(_o,_a,s)=>{if(mode==='abort')controller.abort();else s.api.cancel();}});
  await assert.rejects(s.read({signal:controller.signal}),/cancelled|superseded/);
});

test('NEW compact advancing snapshot expiry after the last native proof refuses publication',async()=>{
  const s=fixture({count:1}),verify=s.api.native.verify;
  s.api.native.verify=async block=>{await verify(block);if(s.proofs===3)s.now=(TIME+120)*1000;};
  await assert.rejects(s.read(),/expired/);assert.equal(s.proofs,3);
});

test('NEW compact final identity cancellation refuses a fully assembled wallet',async()=>{
  const s=fixture({count:1});s.api.identity=async()=>s.api.cancel();await assert.rejects(s.read(),/cancelled|superseded/);
});

test('NEW compact final identity expiry refuses a fully assembled wallet',async()=>{
  const s=fixture({count:1});s.api.identity=async()=>{s.now=(TIME+120)*1000;};await assert.rejects(s.read(),/expired/);
});

for(const mode of ['reorg','confirmation loss'])test('NEW compact '+mode+' after a page cannot yield a successful partial view',async()=>{
  const s=fixture({onFetch:(o,_a,s)=>{if(o===16){if(mode==='reorg')s.currentHash=hash(88);else s.currentHead=BLOCK;}}});
  await assert.rejects(s.read(),/not confirmed/);
});

test('NEW compact captures caller-owned anchor and lifecycle before the first await',async()=>{
  const s=fixture({count:1}),anchor=copy(s.anchor),lifecycle=copy(s.lifecycle);
  const pending=s.api.walletView(OWNER,anchor,{lifecycle});anchor.block_hash=hash(88);lifecycle.new_economic_work_available_by_lifecycle=false;
  const out=await pending;assert.equal(out.inventory.provenance.block_hash,s.anchor.block_hash);assert.deepEqual(out.inventory.lifecycle,s.lifecycle);
});

test('NEW compact HTTP refusal is surfaced once without automatic retry',async()=>{
  const s=fixture({count:1});let attempts=0;s.api.fetcher=async()=>{attempts++;return new Response('{"error":"client_rate_limited"}',{status:429});};
  await assert.rejects(s.read(),error=>error.status===429);assert.equal(attempts,1);
});

for(const status of [429,503])test(`NEW compact later currency HTTP ${status} preserves complete holdings and totals without retry`,async()=>{
  const s=fixture({count:33,assetCount:6}),fetcher=s.api.fetcher;let refusals=0;
  s.api.fetcher=async(url,options)=>{
    if(new URL(url).pathname.endsWith('/0/4')){refusals++;return new Response('{"error":"temporarily_unavailable"}',{status});}
    return fetcher(url,options);
  };
  // Generic503 can mean integrity/history/work refusal. Only the429 variant
  // recovers; the separately NEW exact-service-busy case covers recoverable503.
  if(status===503){await assert.rejects(s.read(),error=>error.status===503&&error.apiCode===undefined);assert.equal(refusals,1);return;}
  const out=await s.read();assert.equal(refusals,1);assert.equal(out.inventory.count,33);assert.equal(out.inventory.complete,true);
  assert.equal(out.earnings,null);assert.match(out.earnings_error,/unavailable/);assert.notEqual(out.totals.lp_usd_18,null);
  assert.deepEqual(s.requests.map(r=>[r.offset,r.assetOffset]),[[0,0],[16,0],[32,0]]);assert.equal(s.identities,1);
});

test('NEW WalletReadGate spaces starts by one monotonic second and keeps FIFO',async()=>{
  let now=0;const starts=[],sleeps=[],gate=new WalletReadGate({clock:()=>now,sleep:async ms=>{sleeps.push(ms);now+=ms;}});
  const jobs=Array.from({length:4},(_,i)=>gate.run(async()=>{starts.push([i,now]);return i;}));
  assert.deepEqual(await Promise.all(jobs),[0,1,2,3]);assert.deepEqual(starts,[[0,0],[1,1000],[2,2000],[3,3000]]);
  assert.deepEqual(sleeps,[1000,1000,1000]);assert.equal(gate.queued,0);
});

test('NEW two API clients at one origin share the same paced read gate',async()=>{
  const key='http://127.0.0.1:4190/new-compact-shared-gate',gate=sharedReadGate(key);assert.equal(sharedReadGate(key),gate);
  let now=0;gate.clock=()=>now;gate.sleep=async ms=>{now+=ms;};const starts=[];
  const first=fixture({count:1}).api,second=fixture({count:1}).api;
  for(const api of [first,second]){api.readGate=gate;api.fetcher=async()=>{starts.push(now);return new Response('{}');};}
  await Promise.all([first.request('/v1/protocol'),second.request('/v1/protocol')]);assert.deepEqual(starts,[0,1000]);
  assert.notEqual(sharedReadGate(key+'/other'),gate);
});

test('NEW WalletReadGate cancellation during pacing never starts cancelled work',async()=>{
  let now=0;const asleep=deferred(),controller=new AbortController();let started=0;
  const gate=new WalletReadGate({clock:()=>now,sleep:async(_ms,signal)=>{asleep.resolve();await new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>reject(Error('cancelled')),{once:true}));}});
  await gate.run(()=>{started++;});const pending=gate.run(()=>{started++;},controller.signal);await asleep.promise;
  controller.abort();await assert.rejects(pending,/cancelled/);assert.equal(started,1);assert.equal(gate.queued,0);
});

test('NEW WalletReadGate has a thirty-two-job bound and no hidden retry',async()=>{
  let now=0;const first=deferred(),gate=new WalletReadGate({clock:()=>now,sleep:async ms=>{now+=ms;}});let starts=0;
  const jobs=[gate.run(async()=>{starts++;await first.promise;})];
  for(let i=1;i<32;i++)jobs.push(gate.run(()=>{starts++;}));
  await assert.rejects(gate.run(()=>{starts++;}),/Too many wallet reads/);first.resolve();await Promise.all(jobs);
  assert.equal(starts,32);assert.equal(gate.queued,0);
  let failures=0;await assert.rejects(gate.run(()=>{failures++;throw Error('read refused');}),/refused/);assert.equal(failures,1);
});

test('NEW WalletReadGate refuses a regressing wake clock instead of starting early',async()=>{
  let now=0;const gate=new WalletReadGate({clock:()=>now,sleep:async()=>{now=999;}});let starts=0;
  await gate.run(()=>{starts++;});await assert.rejects(gate.run(()=>{starts++;}),/scheduler clock/);assert.equal(starts,1);
});

test('NEW actual source10 constructor native graph and NFT validator compose with the compact wire',async()=>{
  const s=source10APISetup('checkpoint2_earnings'),inventory=s.f.outputs.inventory,summary=s.f.outputs.wallet_summary,
    earnings=s.f.outputs.wallet_earnings,anchor=inventory.provenance,assetIds=s.m.reward_assets.map(a=>a.address).sort();
  s.f.outputs.protocol.wallet_view_profile=1;
  const compact={schema:1,kind:'fixed_block_wallet_view_page',available:true,chain_id:s.m.chain_id,wallet:inventory.wallet,
    nft_contract:inventory.nft_contract,count:inventory.count,offset:0,chunk_size:16,token_ids:copy(inventory.token_ids),next_offset:null,
    verified_count:inventory.count,complete:true,
    inventory_sha256:digest(inventory.token_ids),provenance:copy(anchor),history:copy(inventory.history),lifecycle:copy(inventory.lifecycle),
    asset_offset:0,asset_count:assetIds.length,asset_chunk_size:4,asset_ids:assetIds,selected_asset_ids:assetIds,
    asset_inventory_sha256:digest(assetIds),next_asset_offset:null,summary:copy(summary),earnings:copy(earnings),earnings_error:null};
  for(const key of ['asset_offset','asset_count','asset_chunk_size','asset_ids','selected_asset_ids','asset_inventory_sha256','next_asset_offset'])compact.earnings[key]=copy(compact[key]);
  const originalFetch=s.fetcher,paths=[];
  const fetcher=async(url,options)=>{const path=new URL(url).pathname;paths.push(path);return path.includes('/view/')?new Response(JSON.stringify(compact)):originalFetch(url,options);};
  const api=new DeploymentAPI(s.m,{origin:'http://127.0.0.1:4190',reader:s.reader,fetcher,clock:()=>s.now});
  let pacing=0;api.readGate=new WalletReadGate({clock:()=>pacing,sleep:async ms=>{pacing+=ms;}});
  const out=await api.portfolio(inventory.wallet);
  assert.equal(out.financials.inventory.complete,true);assert.equal(out.financials.totals.lp_usd_18,summary.lp_usd_18);
  assert.deepEqual(out.financials.earnings.all_time,earnings.all_time);assert.equal(out.nfts.length,1);assert.equal(out.nfts[0].owner,inventory.wallet);
  assert.ok(paths.some(path=>path.includes('/view/')));assert.equal(paths.filter(path=>path.includes('/view/')).length,1);
  assert.ok(s.calls.some(call=>call.method==='eth_getCode'));assert.ok(s.replySources.includes('produced'));
  assert.equal(s.calls.some(call=>call.method&&/send|sign|nonce|trace|anvil/i.test(call.method)),false);
});

// NEW stage only: exact newly produced Projection/SQLite/ExactReplay compact
// DTOs. Native graph verification below is an explicit synthetic V9 seam;
// the separate earlier constructor case covers its own current native graph.
for(const name of ['1','17','1000','16-65currencies'])test(`NEW producer ${name} exact compact DTOs compose complete browser earnings`,async()=>{
  const f=JSON.parse(await readFile(new URL(`fixtures/compact-wallet-20261121/scenario-${name}.json`,import.meta.url),'utf8'));
  const cfg=f.read_configuration,anchor=f.protocol.provenance,m={schema:4,source_profile:9,accounting_version:7,
    chain_id:cfg.chain_id,deployment_block:cfg.deployment_block,deployment_block_hash:cfg.deployment_block_hash,
    genesis_hash:hash(12),confirmations:cfg.confirmations,max_age_seconds:cfg.max_block_age_seconds,
    projection_sha256:anchor.configuration_sha256,api_prefix:'/api',contracts:cfg.contracts,
    reward_assets:cfg.assets.map(({address,symbol,decimals})=>({address,symbol,decimals}))};
  const api=Object.create(DeploymentAPI.prototype),paths=[],rpc=[];
  Object.assign(api,{manifest:m,origin:'http://127.0.0.1:4190',clock:()=>(anchor.block_timestamp+1)*1000,revision:0,active:null});
  api.native={async verify(block){assert.deepEqual(block,{blockHash:anchor.block_hash,requireCanonical:true});}};
  const stable=value=>Array.isArray(value)?value.map(stable):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(key=>[key,stable(value[key])])):value;
  const key=(method,params)=>method+':'+JSON.stringify(stable(params));
  const recorded=new Map(f.rpc_responses.map(row=>[key(row.method,row.params),row.result]));
  const wire=(method,value)=>{
    const quantity=n=>Number.isSafeInteger(n)&&n>=0?hex(n):n;
    if(['eth_chainId','eth_blockNumber'].includes(method))return quantity(value);
    if(method==='eth_getBlockByNumber'&&value){const header=copy(value);for(const field of ['number','timestamp','gasLimit','gasUsed','baseFeePerGas'])if(field in header)header[field]=quantity(header[field]);return header;}
    return copy(value);
  };
  api.reader={async request({method,params=[]}){
    rpc.push({method,params});assert.doesNotMatch(method,/send|sign|nonce|trace|anvil/i);
    const saved=recorded.get(key(method,params));if(saved!==undefined)return wire(method,saved);
    if(method==='eth_getBlockByNumber'&&params[0]==='0x0')return {number:'0x0',timestamp:'0x0',hash:m.genesis_hash};
    throw Error('No newly produced header or labelled synthetic genesis reply for '+method);
  }};
  api.fetcher=async(url,options)=>{
    const path=new URL(url).pathname.replace(/^\/api/,''),match=path.match(/^\/v1\/wallets\/(0x[0-9a-f]{40})\/view\/(\d+)\/(\d+)\/(\d+)$/);
    paths.push(path);assert.ok(match);assert.equal(match[1],f.owner);assert.equal(Number(match[2]),anchor.block_number);
    assert.equal(options.method,'GET');assert.equal(options.credentials,'omit');
    const page=f.pages.find(row=>row.offset===Number(match[3])&&row.asset_offset===Number(match[4]));assert.ok(page,'Missing exact producer DTO');
    return new Response(JSON.stringify(page));
  };
  const out=await api.walletView(f.owner,copy(anchor),{lifecycle:copy(f.protocol.lifecycle)});
  assert.equal(f.protocol.wallet_view_profile,1);assert.equal(out.inventory.complete,true);assert.deepEqual(out.inventory.token_ids,f.token_ids);
  assert.equal(out.totals.lp_usd_18,f.expected.lp_usd_18);assert.equal(out.totals.claimable_eth_wei,f.expected.claimable_eth_wei);
  assert.equal(out.earnings_error,null);assert.ok(out.earnings);assert.equal(paths.length,f.pages.length);assert.ok(rpc.length>0);
  for(const period of ['all_time','last_24h']){
    assert.equal(out.earnings[period].length,f.descriptor_count);
    for(const row of out.earnings[period])for(const field of fields)assert.equal(row[field+'_raw'],f.expected.raw[period][row.asset][field]);
    for(const field of fields)assert.equal(out.earnings[period+'_usd_at_current_price_18'][field],f.expected.usd[period][field]);
  }
  assert.equal(out.earnings.claims_and_conversions_are_income,false);assert.equal(out.earnings.unprocessed_revenue_included,false);
  if(name==='16-65currencies'){assert.equal(f.descriptor_count,66);assert.equal(f.facts.all_descriptors_fully_priced,true);assert.equal(paths.length,17);}
});

test('NEW producer ASCII currency ordering is independent of String localeCompare',async()=>{
  const s=fixture({count:16,assetCount:6});s.manifest.reward_assets=[...s.assets].reverse();
  const original=String.prototype.localeCompare;
  try{
    String.prototype.localeCompare=()=>{throw Error('Locale-dependent ordering is forbidden');};
    const out=await s.read();assert.deepEqual(out.earnings.all_time.map(row=>row.asset),s.assets.map(asset=>asset.address));
    assert.equal(s.requests.length,2);
  }finally{String.prototype.localeCompare=original;}
});

test('NEW producer portfolio capability and UI branch reuse compact financials without duplicate wallet reads',async()=>{
  const s=fixture({count:1,source:9}),api=s.api;
  s.manifest.canonical_schema=FRESH_CANONICAL_SCHEMA;
  for(const [role,value] of [['access',1],['vault',3],['claim_router',4]])s.manifest.contracts[role]={address:address(value)};
  let capability=1;const paths=[],fetcher=api.fetcher;
  api.fetcher=async(url,options)=>{
    const path=new URL(url).pathname.replace(/^\/api/,'');paths.push(path);
    if(path==='/v1/protocol')return new Response(JSON.stringify({schema:2,chain_id:s.manifest.chain_id,wallet_view_profile:capability,
      provenance:copy(s.anchor),lifecycle:copy(s.lifecycle),minting:{available_by_controls:true},
      contracts:Object.fromEntries(Object.entries(s.manifest.contracts).map(([role,c])=>[role,c.address]))}));
    if(path.startsWith('/v1/nfts/')){const earnings=s.part(0,0).earnings;return new Response(JSON.stringify({...earnings,scope:'nft',token_id:s.ids[0],owner:OWNER}));}
    return fetcher(url,options);
  };
  // This case isolates capability/portfolio/UI routing. Actual native graph
  // and NFT validation execute in the separate earlier constructor method.
  api.nft=async(id,owner)=>({token_id:id,owner,provenance:copy(s.anchor)});
  const out=await api.portfolio(OWNER);
  assert.equal(out.financials.inventory.complete,true);assert.equal(out.financials.earnings.scope,'wallet');
  assert.equal(paths.filter(path=>path.includes('/view/')).length,1);
  assert.equal(paths.some(path=>path.includes('/summary/')||path.includes('/wallets/')&&path.includes('/earnings/')),false);
  const source=await readFile(new URL('../deployment-view.js',import.meta.url),'utf8');
  const begin=source.indexOf('if(data.financials){'),end=source.indexOf('await loadWalletFinancials',begin),branch=source.slice(begin,end);
  assert.ok(begin>=0&&end>begin);assert.match(branch,/totals=data\.financials\.totals/);assert.match(branch,/earnings=data\.financials\.earnings/);
  assert.match(branch,/renderMetrics\(\);\}return;/);
  capability=2;await assert.rejects(api.portfolio(OWNER),/Unsupported wallet view profile/);
  assert.equal(paths.filter(path=>path.includes('/view/')).length,1);
});

test('NEW producer exact service_busy currency refusal preserves complete holdings and totals',async()=>{
  const s=fixture({count:33,assetCount:6}),fetcher=s.api.fetcher;let refused=0;
  s.api.fetcher=async(url,options)=>{
    if(new URL(url).pathname.endsWith('/0/4')){refused++;return new Response('{"error":"service_busy"}',{status:503});}
    return fetcher(url,options);
  };
  const out=await s.read();assert.equal(refused,1);assert.equal(out.inventory.complete,true);assert.equal(out.inventory.count,33);
  assert.notEqual(out.totals.lp_usd_18,null);assert.equal(out.earnings,null);assert.match(out.earnings_error,/unavailable/);
  assert.deepEqual(s.requests.map(row=>row.offset),[0,16,32]);
});

test('NEW producer generic confirmed projection currency refusal fails the complete view',async()=>{
  const s=fixture({count:33,assetCount:6}),fetcher=s.api.fetcher;let refused=0;
  s.api.fetcher=async(url,options)=>{
    if(new URL(url).pathname.endsWith('/0/4')){refused++;return new Response('{"error":"confirmed_projection_unavailable"}',{status:503});}
    return fetcher(url,options);
  };
  await assert.rejects(s.read(),error=>error.status===503&&error.apiCode===undefined);assert.equal(refused,1);
  assert.deepEqual(s.requests.map(row=>row.offset),[0]);
});

for(const mode of ['expiry','cancellation'])test(`NEW producer portfolio final identity ${mode} rejects already assembled financials`,async()=>{
  const s=fixture({count:0,source:9}),api=s.api;s.manifest.canonical_schema=FRESH_CANONICAL_SCHEMA;
  // Isolate the production portfolio's second identity after walletView has
  // closed its own timer. Protocol/canonical native state is explicitly fake.
  api.protocol=async()=>({wallet_view_profile:1,provenance:copy(s.anchor),lifecycle:copy(s.lifecycle)});
  api.identity=async()=>{
    s.identities++;
    if(s.identities===2){if(mode==='expiry')s.now=(TIME+120)*1000;else api.cancel();}
  };
  await assert.rejects(api.portfolio(OWNER),mode==='expiry'?/financial snapshot expired/:/older results were discarded/);
  assert.equal(s.identities,2);assert.equal(s.requests.length,1);
});
