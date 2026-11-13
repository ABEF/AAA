// New20M unsigned-consumer checks only. No old test program is imported.
// Usage: node browser-check.mjs <website checkout> <exclusive scratch directory>
import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const website=resolve(process.argv[2]??''),scratch=resolve(process.argv[3]??'');
assert.ok(process.argv[2]&&process.argv[3],'Explicit source and owned scratch paths required');
const here=new URL('.',import.meta.url),sha=data=>createHash('sha256').update(data).digest('hex');
const inputs=JSON.parse(await readFile(new URL('browser-inputs.json',here),'utf8'));
for(const [name,expected] of Object.entries(inputs.source_sha256))
  assert.equal(sha(await readFile(join(website,name))),expected,'Source changed: '+name);
await mkdir(scratch,{recursive:true});

async function fixtureModule(name,exportNames){
  const file=join(website,'tests',name),url=pathToFileURL(file),text=await readFile(file,'utf8');
  const boundary=text.indexOf('for(const policy of [1,2])test(');
  assert.ok(boundary>0,'Known fixture boundary missing');
  const original=text.slice(0,boundary);
  assert.ok(!/(?<![.\w])test\s*\(/.test(original),'Do not register old tests');
  let body=original.replace("import test from 'node:test';",'');
  body=body.replace(/from (['"])(\.[^'"]+)\1/g,(_m,_q,path)=>`from '${new URL(path,url).href}'`);
  // Preserve source9's archived JSON fixture location after moving its factories.
  body=body.replace(/new URL\('(\.\/fixtures\/[^']+)',import\.meta\.url\)/g,
    (_m,path)=>`new URL('${new URL(path,url).href}')`);
  body+=`\nexport {${exportNames.join(',')}};\n`;
  const generated=join(scratch,name.replace('.test.mjs','.factories.mjs'));
  await writeFile(generated,body,{flag:'wx'});
  return {module:await import(pathToFileURL(generated).href),
    evidence:{source:'tests/'+name,source_sha256:sha(text),
      prefix_sha256:sha(original),generated_sha256:sha(body),old_tests_registered:0}};
}
const v10=await fixtureModule('source10-prepare.test.mjs',['entry','fixture']);
const v9=await fixtureModule('source9-prepare.test.mjs',['entrySetup','setup']);
const {prepareFresh}=await import(pathToFileURL(join(website,'deployment-source9-prepare.js')).href);
const cases=[],add=(name,run)=>cases.push({name,run}),hex=n=>'0x'+BigInt(n).toString(16);

function profile20(s,{estimate=16_000_000n,configured=20_000_000,block=32_000_000}={}){
  s.m.activation_policy_schema=2;s.m.limits.gas=20_000_000;
  s.m.limits.gas_price_wei='2';s.m.limits.network_fee_wei='40000000';
  s.price=2n;s.estimate=estimate;s.blockLimit=block;s.draft.schema=2;
  const suggested=(estimate*120n+99n)/100n,effective=Math.min(configured,block);
  Object.assign(s.draft.network_gas,{policy_schema:2,estimated_units:estimate.toString(),
    suggested_limit:suggested.toString(),price_wei:'2',estimated_fee_wei:(estimate*2n).toString(),
    suggested_limit_cost_wei:(suggested*2n).toString(),configured_gas_limit:String(configured),
    confirmed_block_gas_limit:String(block),effective_gas_limit:String(effective),
    full_twenty_percent_headroom:true});
  return s;
}
async function current(options={}){
  const s=v10.module.entry({...options,policy:2,execution:1});await s.termsPromise;
  return profile20(s);
}

for(const options of [{asset:'ETH'},{asset:'ZZZ'},{asset:'ETH',action:'increase'},
                     {asset:'ZZZ',action:'increase'},{asset:'ZZZ',approval:true}])
  add('source10/execution1 unsigned20M '+JSON.stringify(options),async()=>{
    const s=await current(options),review=await prepareFresh(s.api,s.intent);
    assert.equal(review.network_gas.gas_limit,'19200000');assert.equal(review.signing_enabled,false);
    assert.equal(review.transaction.nonce,undefined);assert.equal(review.transaction.gas,undefined);
    assert.deepEqual(review.transaction,s.draft.transaction);
    const checks=s.calls.filter(c=>['eth_call','eth_estimateGas'].includes(c.method)&&c.params[0]?.from);
    assert.ok(checks.length>=2);assert.ok(checks.every(c=>c.params[0].gas===hex(20_000_000)));
  });

add('historical source9 accepts explicit20M without adopting execution1',async()=>{
  const s=profile20(v9.module.entrySetup({asset:'ETH'}));
  const review=await prepareFresh(s.api,s.intent);
  assert.equal(review.signing_enabled,false);assert.equal(review.network_gas.gas_limit,'19200000');
  assert.equal(s.m.execution_price_version,undefined);assert.equal(s.m.lp_routing_version,2);
});

for(const configured of [19_000_000,21_000_000])
  add('source10 rejects backend configured cap '+configured+' versus manifest20M',async()=>{
    const s=await current();profile20(s,{configured});
    await assert.rejects(prepareFresh(s.api,s.intent),/policy2/);
  });

add('full20pct at20M is accepted but one estimated unit above rejects',async()=>{
  const good=await current();profile20(good,{estimate:16_666_666n});
  const result=await prepareFresh(good.api,good.intent);
  assert.equal(result.network_gas.gas_limit,'20000000');
  const bad=await current();profile20(bad,{estimate:16_666_667n});
  await assert.rejects(prepareFresh(bad.api,bad.intent),/Gas, headroom/);
});

add('fee ceiling remains binding independently of20M',async()=>{
  const s=await current();s.m.limits.network_fee_wei='38399999';
  await assert.rejects(prepareFresh(s.api,s.intent),/Gas, headroom/);
});

add('unknown block or independent estimate refusal does not produce review',async()=>{
  for(const failure of ['eth_getBlockByNumber','eth_estimateGas']){
    const s=await current();s.rpcHook=method=>{if(method===failure)throw Error('Injected provider refusal');};
    await assert.rejects(prepareFresh(s.api,s.intent),/Injected provider refusal/);
    assert.equal(s.m.limits.gas,20_000_000);
  }
});

add('activation20M leaves claim policy1 capped at12M',async()=>{
  const healthy=v10.module.fixture({execution:1});healthy.m.activation_policy_schema=2;healthy.m.limits.gas=20_000_000;
  const review=await prepareFresh(healthy.api,healthy.intent);
  assert.equal(review.signing_enabled,false);assert.equal(review.network_gas.gas_limit,'120000');
  const over=v10.module.fixture({execution:1});over.m.activation_policy_schema=2;over.m.limits.gas=20_000_000;
  over.estimate=11_000_000n;
  Object.assign(over.draft.network_gas,{estimated_units:'11000000',suggested_limit:'13200000',
    estimated_fee_wei:(11_000_000n*over.price).toString(),suggested_limit_cost_wei:(13_200_000n*over.price).toString()});
  await assert.rejects(prepareFresh(over.api,over.intent),/Gas, headroom/);
});

const selected=process.argv[4]?JSON.parse(await readFile(process.argv[4],'utf8')):null;
if(selected){assert.ok(Array.isArray(selected)&&selected.length>0);assert.ok(selected.every(name=>cases.some(c=>c.name===name)));}
const results=[];
for(const item of cases.filter(item=>!selected||selected.includes(item.name))){
  try{await item.run();results.push({name:item.name,status:'pass'});}
  catch(error){results.push({name:item.name,status:'fail',message:error.message,stack:error.stack});}
}
const record={scope:'New20M consumer checks with actual website source and injected typed fixtures; no old tests, signer, network or site changes',
  fixture_factories:[v10.evidence,v9.evidence],source_sha256:inputs.source_sha256,
  cases:results,passed:results.filter(x=>x.status==='pass').length,failed:results.filter(x=>x.status==='fail').length};
await writeFile(join(scratch,'RESULT.json'),JSON.stringify(record,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(record,null,2));if(record.failed)process.exitCode=1;
