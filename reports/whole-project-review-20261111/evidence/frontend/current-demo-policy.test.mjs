import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import * as d from '../domain.js';
import {previewChange} from '../preview-store.js';
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const legacy=[{type:'claim',ids:[444]},{type:'mint'},
 {type:'activate',id:1001,amount:100,pool:'ZZZ/WETH',fundingAsset:'USDC'},
 {type:'increase',id:1001,amount:0.01,fundingAsset:'USDG'},
 {type:'claim',ids:[128],scope:'all'}];

test('current demo policy selects ETH/ZZZ, one native pair and3percent total contribution',()=>{
  assert.deepEqual(d.CURRENT_FUNDING_ASSETS,['ETH','ZZZ']);
  assert.equal(d.CURRENT_CONTRIBUTION_POOL,'ZZZ/ETH');assert.equal(d.CURRENT_CONTRIBUTION_LOSS_BPS,300);assert.equal(d.CURRENT_DEMO_POLICY,2);
});
test('current activation and growth accept ETH/ZZZ without changing prior rewards',()=>{
  for(const asset of ['ETH','ZZZ']){
    const before=d.buildDemoCollection(),n=before.find(n=>!n.lockedCents&&n.exampleOwned);
    const activated=d.activateCurrentPreview(before,{id:n.id,amount:100,fundingAsset:asset}).collection;
    const after=d.increaseCurrentPreview(activated,{id:n.id,amount:5,fundingAsset:asset}).collection;
    const item=after.find(x=>x.id===n.id);assert.equal(item.pool,'ZZZ/ETH');assert.equal(item.lockedCents,10500);assert.equal(d.claimable(item),0);
    assert.equal(hash(before),'52ead56bd450875c0195d341c66b3c35065afd109199e985fe7868f65509c96a');
  }
});
test('current writes reject removed currencies, old pools and subminimum growth',()=>{
  const before=d.buildDemoCollection(),id=before.find(n=>!n.lockedCents&&n.exampleOwned).id;
  for(const fundingAsset of ['USDC','USDG','WETH',undefined])assert.throws(()=>d.activateCurrentPreview(before,{id,amount:100,fundingAsset}),/ETH or ZZZ/);
  for(const pool of ['ZZZ/WETH','ZZZ/USDC','bad'])assert.throws(()=>d.activateCurrentPreview(before,{id,amount:100,fundingAsset:'ETH',pool}),/current ETH\/ZZZ/);
  for(const amount of [0.01,4.99,NaN,Infinity])assert.throws(()=>d.increaseCurrentPreview(before,{id:444,amount,fundingAsset:'ETH'}));
  assert.equal(hash(before),'52ead56bd450875c0195d341c66b3c35065afd109199e985fe7868f65509c96a');
});
test('the exact prior seed, storage key and unversioned legacy ledger remain byte-equivalent',()=>{
  assert.equal(d.STORAGE_KEY,'zzz-popl-preview-v7');
  assert.equal(hash(d.buildDemoCollection()),'52ead56bd450875c0195d341c66b3c35065afd109199e985fe7868f65509c96a');
  const result=d.replayEvents(legacy);assert.equal(hash(result),'217d865c092f742578e1e1301dec66ed56bba7cbf4023336ab1c56060a010cb4');
  const activated=result.find(n=>n.id===1001);assert.equal(activated.pool,'ZZZ/WETH');assert.equal(activated.activationAsset,'USDC');assert.equal(activated.lockedCents,10001);
});
test('current versioned events replay alongside old events and reject unknown policies',()=>{
  const before=d.replayEvents(legacy),id=before.find(n=>!n.lockedCents&&n.exampleOwned).id;
  const event={type:'activate',id,amount:100,fundingAsset:'ETH',pool:'ZZZ/ETH',demo_policy:2};
  const result=previewChange(before,event).collection;assert.deepEqual(d.replayEvents([...legacy,event]),result);
  const topup={type:'increase',id,amount:5,fundingAsset:'ZZZ',pool:'ZZZ/ETH',demo_policy:2};
  assert.deepEqual(d.replayEvents([...legacy,event,topup]),previewChange(result,topup).collection);
  assert.throws(()=>previewChange(before,{...event,demo_policy:3}),/Unknown demo/);
  assert.throws(()=>previewChange(before,{...event,fundingAsset:'USDC'}),/ETH or ZZZ/);
  assert.deepEqual(d.replayEvents([...legacy,{...event,demo_policy:3}]),before);
});
test('public demo copy and new-intent entrypoint no longer advertise removed input choices',async()=>{
  const html=await readFile(new URL('../index.html',import.meta.url),'utf8');
  const app=await readFile(new URL('../app.js',import.meta.url),'utf8');
  assert.doesNotMatch(html,/USDC|USDG|99%/);assert.match(html,/at least 97% deployed/);
  assert.match(app,/CURRENT_FUNDING_ASSETS\.map/);assert.match(app,/demo_policy:CURRENT_DEMO_POLICY/);
  assert.doesNotMatch(app,/<option value="(?:USDC|USDG)"|pool='ZZZ\/WETH'|At least 99%/);
});
