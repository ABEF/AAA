import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeSetup,nativeFixtureNames} from './helpers/deployment-native-fixture.mjs';
export {nativeSetup} from './helpers/deployment-native-fixture.mjs';
import {DeploymentAPI,validateDeployment,ZERO,ZERO_HASH} from '../deployment-api.js';
import {NativeProfile,NATIVE_ROLES} from '../deployment-native.js';
const address=n=>'0x'+BigInt(n).toString(16).padStart(40,'0'),hash=c=>'0x'+c.repeat(64),word=n=>BigInt(n).toString(16).padStart(64,'0'),aw=a=>a.slice(2).padStart(64,'0');
const copy=x=>structuredClone(x),block={blockHash:hash('b'),requireCanonical:true};
function setup(){
  const contracts=Object.fromEntries(NATIVE_ROLES.map((role,i)=>[role,{address:address(i+1),runtime_code:'0x60'+(i+1).toString(16).padStart(2,'0')}]));
  const asset={symbol:'ETH',address:ZERO,decimals:18,valuation_asset:ZERO,route_id:ZERO_HASH,route_kind:0,enabled:true,runtime_code:null,price_policy_id:hash('3'),asset_policy_id:hash('4')};
  const manifest={schema:2,mode:'read-and-prepare',environment:'production',id:'d'.repeat(64),accounting_version:2,pricing_version:2,routing_version:2,review_policy_version:1,chain_id:46630,chain_name:'Robinhood',genesis_hash:hash('c'),deployment_block:10,deployment_block_hash:hash('a'),confirmations:12,max_age_seconds:120,api_prefix:'/api',rpc_url:'https://rpc.example.org',projection_sha256:'1'.repeat(64),transaction_sha256:'2'.repeat(64),activation_sha256:'3'.repeat(64),transaction_fee_review:hash('8'),activation_fee_review:hash('9'),contracts,pool_id:hash('f'),input_assets:[asset],reward_assets:[{address:ZERO,symbol:'ETH',decimals:18}],limits:{gas:12000000,gas_price_wei:'1000000000',network_fee_wei:'10000000000000000',native_value_wei:'1000000000000000000',contribution_usd_18:'1000000000000000000000',maximum_contribution_loss_bps:200}};
  const replies=new Map(),calls=[],set=(role,data,...values)=>replies.set(contracts[role].address+':'+data,'0x'+values.map(v=>typeof v==='string'?v:word(v)).join(''));
  for(const [role,selector,wanted] of [['vault','0xebbc42b6',2],['oracle','0x5f9c8132',2],['entry','0x96b09228',1],['contribution_pricing','0x49de0529',1],['budget','0xc187241c',1000],['contribution_pricing','0x02fb0c5e',0]])set(role,selector,wanted);
  for(const [role,selector,target] of [['vault','0x7d13e4db','budget'],['vault','0x71907f17','access'],['nft','0x71907f17','access'],['nft','0xbc1bc485','claim_router'],['claim_router','0x71907f17','access'],['claim_router','0x47ccca02','nft'],['budget','0xfbfa77cf','vault'],['budget','0x71907f17','access'],['oracle','0x2cf518cc','contribution_pricing'],['oracle','0x71907f17','access'],['contribution_pricing','0x7dc0d1d0','oracle'],['contribution_pricing','0x71907f17','access'],['entry','0x7b103999','pools'],['entry','0x5b703199','activation_assets'],['entry','0x71907f17','access'],['pools','0x5dbf78a2','entry'],['pools','0x5b703199','activation_assets'],['pools','0x71907f17','access'],['activation_assets','0x7b103999','pools'],['activation_assets','0x71907f17','access']])set(role,selector,aw(contracts[target].address));
  for(const [role,id] of [['vault','411f1fc1c0e7b1fef9670835d6b39dd39cdfaadfae26102258b61be58c80b968'],['nft','86798dfd34b3cf289e7582d0460beda645ea24721422547e964271fa9bdb63e5'],['oracle','bf820fa66fadba8f93ff177e73b8d9962881eaa782ee4924feadac7ed13eaf38'],['pools','e172fc22ef4736794abb342530a7acc3f7d6bbf4f70bb0141fa0aa0eaa39a6a7']])set('access','0xe8cffd1d'+id,aw(contracts[role].address));
  set('budget','0xa7b5810c',200);set('oracle','0x237a06fb'+aw(ZERO),asset.price_policy_id.slice(2));
  set('activation_assets','0x237a06fb'+aw(ZERO),asset.asset_policy_id.slice(2));
  set('oracle','0x8ee573ac'+aw(ZERO),18);set('oracle','0x4cbb3d60'+aw(ZERO),1000n*10n**18n,1030n*10n**18n,hash('5').slice(2));
  set('activation_assets','0xddbfd8ef'+asset.asset_policy_id.slice(2),aw(ZERO),1,hash('6').slice(2),hash('7').slice(2),18,1);
  set('entry','0x2e4c02f3'+ZERO_HASH.slice(2),0);
  const reader={request:async({method,params})=>{
    calls.push({method,params});assert.ok(!/send|sign|anvil/i.test(method));
    if(method==='eth_getCode'){assert.deepEqual(params[1],block);return Object.values(contracts).find(c=>c.address===params[0])?.runtime_code??'0x';}
    if(method==='eth_call'){assert.deepEqual(params[1],block);const value=replies.get(params[0].to+':'+params[0].data);if(value===undefined)throw Error('Unexpected getter '+params[0].data);return value;}
    throw Error('Unexpected method '+method);
  }};
  return {manifest,asset,replies,calls,set,reader,profile:()=>new NativeProfile(validateDeployment(manifest,'https://app.example.org'),reader)};
}
test('schema2 native manifest requires explicit versions, ceiling, policy IDs and true ETH identity',()=>{
  const s=setup();assert.equal(validateDeployment(s.manifest,'https://app.example.org').input_assets[0].valuation_asset,ZERO);
  for(const mutate of [m=>delete m.pricing_version,m=>m.review_policy_version=0,m=>m.routing_version=1,m=>delete m.limits.maximum_contribution_loss_bps,m=>m.limits.maximum_contribution_loss_bps=1001,m=>m.input_assets[0].runtime_code='0x6000',m=>m.input_assets[0].valuation_asset=address(20),m=>delete m.input_assets[0].price_policy_id,m=>m.input_assets[0].asset_policy_id=ZERO_HASH,m=>m.input_assets[0].route_kind=1]){const m=copy(s.manifest);mutate(m);assert.throws(()=>validateDeployment(m,'https://app.example.org'));}
  const downgrade=copy(s.manifest);downgrade.schema=1;assert.throws(()=>validateDeployment(downgrade,'https://app.example.org'));
});
test('native read verifies parents/versions once per exact confirmed block and never requests ETH runtime',async()=>{
  const s=setup(),p=s.profile();const result=await p.price(s.asset,block);assert.equal(result.lower,1000n*10n**18n);assert.equal(result.upper,1030n*10n**18n);assert.equal(await p.cap(block),200);
  assert.equal(s.calls.filter(c=>c.method==='eth_getCode').length,10);assert.ok(s.calls.every(c=>c.method!=='eth_getCode'||c.params[0]!==ZERO));
  await p.verify(block);assert.equal(s.calls.filter(c=>c.method==='eth_getCode').length,10);
});
test('valid runtime at wrong parent, wrong version or missing getter cannot obtain native readiness',async()=>{
  for(const change of [s=>s.set('budget','0xfbfa77cf',aw(address(99))),s=>s.set('entry','0x96b09228',0),s=>s.replies.set(s.manifest.contracts.oracle.address+':0x5f9c8132','0x')]){const s=setup();change(s);await assert.rejects(s.profile().verify(block));}
});
test('native cap reads current governed value under the explicitly approved ceiling, including zero',async()=>{
  for(const n of [0,100,200]){const s=setup();s.set('budget','0xa7b5810c',n);assert.equal(await s.profile().cap(block),n);}
  for(const n of [201,1001]){const s=setup();s.set('budget','0xa7b5810c',n);await assert.rejects(s.profile().cap(block),/ceiling/);}
});
test('changed source price or admission identity never silently falls back to another policy',async()=>{
  for(const change of [s=>s.set('oracle','0x237a06fb'+aw(ZERO),hash('e').slice(2)),s=>s.set('activation_assets','0x237a06fb'+aw(ZERO),hash('e').slice(2)),s=>s.set('oracle','0x8ee573ac'+aw(ZERO),6),s=>s.set('activation_assets','0xddbfd8ef'+s.asset.asset_policy_id.slice(2),aw(ZERO),0,hash('6').slice(2),hash('7').slice(2),18,1)]){const s=setup();change(s);await assert.rejects(s.profile().price(s.asset,block));}
});
test('dual bounds reject zero, inverted, oversized, missing fingerprint and malformed ABI',async()=>{
  for(const values of [[0n,1n,hash('5').slice(2)],[2n,1n,hash('5').slice(2)],[1n,10n**36n+1n,hash('5').slice(2)],[1n,1n,ZERO_HASH.slice(2)]]){const s=setup();s.set('oracle','0x4cbb3d60'+aw(ZERO),...values);await assert.rejects(s.profile().price(s.asset,block));}
  const s=setup();s.set('oracle','0x4cbb3d60'+aw(ZERO),1);await assert.rejects(s.profile().price(s.asset,block),/malformed/);
});
test('schema2 supports the complete49-currency union without increasing native ledger bounds',()=>{
  const s=setup();s.manifest.reward_assets=Array.from({length:49},(_,i)=>({address:i?address(100+i):ZERO,symbol:i?'ZZZ':'ETH',decimals:18}));
  assert.equal(validateDeployment(s.manifest,'https://app.example.org').reward_assets.length,49);
  s.manifest.reward_assets.push({address:address(999),symbol:'ZZZ',decimals:18});assert.throws(()=>validateDeployment(s.manifest,'https://app.example.org'));
});
test('staged native read API has no submission capability and keeps public profiles unsigned',()=>{
  const s=setup(),api=new DeploymentAPI(s.manifest,{origin:'https://app.example.org',reader:s.reader,fetcher:async()=>{throw Error('No request expected');}});
  assert.equal(typeof api.send,'undefined');assert.equal(typeof api.sign,'undefined');assert.ok(api.native instanceof NativeProfile);
});

for(const name of nativeFixtureNames)test('actual current Python native DTO independently reconstructs '+name,async()=>{
  const s=nativeSetup(name),review=await s.api.prepare(s.intent);
  assert.deepEqual(review.transaction,s.f.draft.transaction);assert.equal(review.signing_enabled,false);
  if(name==='claim_eth_both'){
    assert.equal(review.action,'claim');assert.equal(review.source,null);assert.equal(review.claims.length,2);
    assert.deepEqual(review.claims.map(c=>c.royalty),[false,true]);assert.ok(review.claims.every(c=>c.asset===ZERO));
    assert.equal(review.claims[0].view_raw,'30000000000000000');return;
  }
  assert.equal(review.execution_limit_bps,200);assert.equal(review.reviewed_maximum_loss_bps,200);
  assert.equal(review.price_bounds.asset,s.m.input_assets[0].address);assert.equal(review.source_upper_usd_18,'100000000000000000000');
  if(name.startsWith('approve')){assert.equal(review.action,'approve');assert.equal(review.transaction.data.length,138);}
  else {assert.equal(review.transaction.data.slice(0,10),'0x7d2edfe7');assert.equal(review.transaction.data.length,650);assert.equal(review.transaction.data.slice(-64),word(200));}
});
for(const [label,change] of [
  ['old selector',s=>s.f.draft.transaction.data='0x35b13b87'+s.f.draft.transaction.data.slice(10,-64)],
  ['changed caller maximum',s=>s.f.draft.transaction.data=s.f.draft.transaction.data.slice(0,-64)+word(201)],
  ['reported caller maximum',s=>s.f.draft.reviewed_maximum_loss_bps=201],
  ['reported captured cap',s=>s.f.draft.execution_limit_bps=100],
  ['loss floor',s=>s.f.draft.minimum_deployed_usd_18='97000000000000000000'],
  ['pricing profile',s=>s.f.draft.provenance.pricing_version=1],
  ['missing review profile',s=>delete s.f.draft.provenance.review_policy_version],
  ['read accounting downgrade',s=>s.f.protocol.provenance.accounting_version=1],
  ['NFT accounting missing',s=>delete s.f.nft.provenance.accounting_version],
  ['governed cap widened',s=>s.set('budget','0xa7b5810c','0x'+word(201))],
  ['unreviewed Oracle policy',s=>s.set('oracle','0x237a06fb'+aw(ZERO),hash('e'))],
  ['changed pricing parent',s=>s.set('contribution_pricing','0x7dc0d1d0','0x'+aw(address(99)))],
])test('native unsigned preparation rejects '+label,async()=>{const s=nativeSetup('activate_eth',change);await assert.rejects(s.api.prepare(s.intent));});
test('native typed-v4 route disable or kind substitution cannot become a valid review',async()=>{
  for(const change of [s=>s.set('entry','0x2e4c02f3'+s.f.route.slice(2),'0x'+word(1)),s=>s.set('entry','0x2e59691a'+s.f.route.slice(2),'0x'+word(0))]){const s=nativeSetup('activate_usdg',change);await assert.rejects(s.api.prepare(s.intent));}
});
test('synthetic source bounds use upper-input budget, never lower-only98 instead of98.98',async()=>{
  const s=nativeSetup();const result=s.rpc.get(s.pins.oracle+':0x4cbb3d60'+aw(ZERO));
  s.set('oracle','0x4cbb3d60'+aw(ZERO),'0x'+word(10n**18n)+word(101n*10n**16n)+result.slice(-64));
  const floor='98980000000000000000';s.f.draft.minimum_deployed_usd_18=floor;s.f.draft.contribution.required_deployed_usd_18=floor;
  const review=await s.api.prepare(s.intent);assert.equal(review.source_upper_usd_18,'101000000000000000000');assert.equal(review.minimum_deployed_usd_18,floor);
  s.f.draft.minimum_deployed_usd_18='98000000000000000000';await assert.rejects(s.api.prepare(s.intent),/review differs/);
});
test('synthetic raw-unit input rounds its upper USD mark upward before applying the floor',async()=>{
  const s=nativeSetup('increase_eth'),amount=5n*10n**18n+1n,upperPrice=10n**18n+1n;
  const upper=(amount*upperPrice+10n**18n-1n)/10n**18n,floor=upper-upper*200n/10000n;
  assert.equal(upper,5n*10n**18n+7n);s.intent.amount='5.000000000000000001';
  const bounds=s.rpc.get(s.pins.oracle+':0x4cbb3d60'+aw(ZERO));s.set('oracle','0x4cbb3d60'+aw(ZERO),'0x'+word(10n**18n)+word(upperPrice)+bounds.slice(-64));
  const d=s.f.draft;d.source.amount_raw=amount.toString();d.source.value_usd_18=amount.toString();d.minimum_deployed_usd_18=floor.toString();d.contribution.source_usd_18=amount.toString();d.contribution.required_deployed_usd_18=floor.toString();
  for(const k of ['marginal_deployed_usd_18','net_contribution_usd_18','shares_added_raw'])d.contribution[k]=amount.toString();
  const words=d.transaction.data.slice(10).match(/.{64}/g);words[3]=word(amount);d.transaction.data='0x7d2edfe7'+words.join('');d.transaction.value='0x'+amount.toString(16);
  assert.equal((await s.api.prepare(s.intent)).source_upper_usd_18,upper.toString());
  d.minimum_deployed_usd_18=(floor-1n).toString();await assert.rejects(s.api.prepare(s.intent));
});
test('synthetic zero and1000bps policies are explicit, correctly encoded and never inferred',async()=>{
  for(const cap of [0,1000]){
    const s=nativeSetup('activate_eth',s=>{s.m.limits.maximum_contribution_loss_bps=1000;s.set('budget','0xa7b5810c','0x'+word(cap));});
    const d=s.f.draft,floor=100n*10n**18n-100n*10n**18n*BigInt(cap)/10000n;
    d.execution_limit_bps=cap;d.reviewed_maximum_loss_bps=cap;d.minimum_deployed_usd_18=floor.toString();d.contribution.required_deployed_usd_18=floor.toString();
    for(const k of ['marginal_deployed_usd_18','net_contribution_usd_18','shares_added_raw'])d.contribution[k]='100000000000000000000';
    d.transaction.data=d.transaction.data.slice(0,-64)+word(cap);
    const r=await s.api.prepare(s.intent);assert.equal(r.execution_limit_bps,cap);assert.equal(r.transaction.data.slice(-64),word(cap));
  }
});
test('unavailable contribution price read does not block unrelated confirmed NFT reads',async()=>{
  const s=nativeSetup('increase_eth');s.set('oracle','0x4cbb3d60'+aw(ZERO),'0x');
  assert.equal((await s.api.nft(s.intent.id,s.intent.account)).token_id,s.intent.id);
  await assert.rejects(s.api.prepare(s.intent),/malformed/);
});
test('a cap above this client review ceiling stops contribution reviews, not ordinary position reads',async()=>{
  const s=nativeSetup('increase_eth');s.set('budget','0xa7b5810c','0x'+word(201));
  assert.equal((await s.api.nft(s.intent.id,s.intent.account)).owner,s.intent.account);
  await assert.rejects(s.api.prepare(s.intent),/ceiling/);
});
test('a legacy manifest rejects declared native protocol and NFT data instead of guessing a profile',async()=>{
  const s=nativeSetup('activate_eth',s=>{
    s.m.schema=1;for(const key of ['accounting_version','pricing_version','routing_version','review_policy_version'])delete s.m[key];
    for(const key of ['pools','budget','activation_assets','contribution_pricing'])delete s.m.contracts[key];
    s.m.input_assets[0].valuation_asset=address(20);
  });
  await assert.rejects(s.api.protocol(),/legacy/);await assert.rejects(s.api.nft(s.f.nft.token_id,s.f.nft.owner),/legacy/);
});
test('native combined claims reject omitted LP entitlement or a substituted royalty selection',async()=>{
  for(const change of [s=>s.f.draft.claim_operations.shift(),s=>s.f.draft.claim_operations[0].royalty=true]){
    const s=nativeSetup('claim_eth_both',change);await assert.rejects(s.api.prepare(s.intent),/selection/);
  }
});
test('native manifest cannot omit ETH from its reviewed reward inventory',()=>{
  assert.throws(()=>nativeSetup('claim_eth_both',s=>{s.m.reward_assets=s.m.reward_assets.filter(a=>a.address!==ZERO);}),/Native reward inventory/);
});
test('missing ETH in either native claim ledger rejects reads and claims before a partial total can appear',async()=>{
  for(const scope of ['lp','royalties']){
    const s=nativeSetup('claim_eth_both',s=>{s.f.nft.claimable[scope]=s.f.nft.claimable[scope].filter(a=>a.asset!==ZERO);});
    await assert.rejects(s.api.nft(s.f.nft.token_id,s.f.nft.owner),/Native ledger omitted ETH/);
    await assert.rejects(s.api.prepare(s.intent),/Native ledger omitted ETH/);
    assert.ok(s.calls.every(c=>!c.path?.endsWith('/prepare')),'No partial-claim draft should be requested');
  }
});
function portfolioEarnings(s){
  const fields=['lp_individual','lp_collective','royalties'],p=copy(s.f.nft.provenance);
  const report={schema:1,chain_id:31337,scope:'nft',token_id:s.f.nft.token_id,owner:s.f.nft.owner,available:true,claims_and_conversions_are_income:false,unprocessed_revenue_included:false,clock:'on-chain processing/allocation time',provenance:p,window:{after_timestamp_exclusive:Math.max(-1,p.block_timestamp-86400),through_timestamp_inclusive:p.block_timestamp}};
  for(const period of ['all_time','last_24h']){
    report[period]=s.m.reward_assets.map(a=>({asset:a.address,symbol:a.symbol,decimals:a.decimals,current_price:{available:true,usd_per_token_18:'1000000000000000000'},...Object.fromEntries(fields.map(k=>[k+'_raw','0'])),usd_at_current_price_18:Object.fromEntries(fields.map(k=>[k,'0']))}));
    report[period+'_usd_at_current_price_18']=Object.fromEntries(fields.map(k=>[k,'0']));
  }
  const inventory={schema:2,chain_id:31337,wallet:s.f.nft.owner,nft_contract:s.pins.nft,available:true,count:1,token_ids:[s.f.nft.token_id],provenance:p};
  const request=s.api.request.bind(s.api);s.api.request=(path,...args)=>path.includes('/wallets/')?Promise.resolve(inventory):path.endsWith('/earnings')?Promise.resolve(report):request(path,...args);
  return report;
}
test('portfolio attaches complete validated NFT earnings without changing confirmed LP',async()=>{
  const s=nativeSetup('increase_eth'),earned=portfolioEarnings(s),result=await s.api.portfolio(s.f.nft.owner);
  assert.equal(result.nfts[0].earnings,earned);assert.equal(result.nfts[0].earnings.available,true);
  assert.equal(result.nfts[0].position.current_lp_value.raw,s.f.nft.position.current_lp_value.raw);
});
for(const [label,change] of [
  ['malformed raw amount',r=>r.all_time[0].lp_individual_raw='1e18'],
  ['invalid current price',r=>r.all_time[0].current_price.usd_per_token_18='0'],
  ['inflated USD total',r=>r.all_time_usd_at_current_price_18.lp_individual='1000000000000000000']
])test('portfolio treats '+label+' as unavailable earnings while retaining LP',async()=>{
  const s=nativeSetup('increase_eth'),earned=portfolioEarnings(s);change(earned);
  const result=await s.api.portfolio(s.f.nft.owner);assert.equal(result.nfts[0].earnings.available,false);
  assert.equal(result.nfts[0].position.current_lp_value.raw,s.f.nft.position.current_lp_value.raw);
  assert.equal(result.nfts[0].owner,s.f.nft.owner);
});
