#!/usr/bin/env node
// Actual HTTP/RPC composition of an explicitly selected external website checkout.
// This process has no signer, nonce, broadcast, fixture or provider-override path.
import {createHash} from 'node:crypto';
import {open,readFile,realpath,stat} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const OPTIONS=['website-root','manifest','origin','cases','output'];
const RPC_READS=new Set(['eth_chainId','eth_blockNumber','eth_getBlockByNumber','eth_getCode',
  'eth_call','eth_estimateGas','eth_gasPrice','eth_getBalance']);
const ADDRESS=/^0x[0-9a-f]{40}$/;
const ZERO='0x'+'0'.repeat(40);
const REJECTION_STAGES=new Set(['read_protocol','read_nft','activation_quote','prepare']);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const requireThat=(condition,message)=>{if(!condition)throw Error(message);};
const usage='Usage: node rehearse-source9-consumer.mjs --website-root ABSOLUTE_PATH --manifest JSON --origin http://127.0.0.1:PORT --cases JSON --output NEW_JSON';

function argumentsOf(argv){
  if(argv.length===1&&argv[0]==='--help')return null;
  const result={};
  for(let i=0;i<argv.length;i+=2){
    const key=argv[i]?.slice(2);
    requireThat(argv[i]?.startsWith('--')&&OPTIONS.includes(key)&&argv[i+1]&&!Object.hasOwn(result,key),'Invalid or repeated command-line option.');
    result[key]=argv[i+1];
  }
  requireThat(OPTIONS.every(key=>Object.hasOwn(result,key)),'All five reviewed inputs are required.');
  requireThat(path.isAbsolute(result['website-root']),'Website root must be an absolute path.');
  return result;
}

function loopback(value,{origin=false}={}){
  requireThat(typeof value==='string'&&/^http:\/\/127\.0\.0\.1(?::[1-9][0-9]{0,4})?(?:\/[^?#]*)?$/.test(value),
    'Only literal 127.0.0.1 HTTP rehearsal endpoints are permitted.');
  const url=new URL(value);
  requireThat(url.protocol==='http:'&&url.hostname==='127.0.0.1'&&!url.username&&!url.password&&!url.search&&!url.hash&&
    (!origin||url.pathname==='/'),'Only literal 127.0.0.1 HTTP rehearsal endpoints are permitted.');
  return origin?url.origin:url.href;
}

function validRejection(value){
  if(!object(value)||Object.keys(value).some(key=>!['stage','category','http_status','message'].includes(key))||
    !REJECTION_STAGES.has(value.stage)||!['consumer_validation','http'].includes(value.category)||
    value.message!==undefined&&(typeof value.message!=='string'||!value.message.length||value.message.length>300||/[\x00-\x1f\x7f]/.test(value.message)))return false;
  if(value.category==='consumer_validation')return typeof value.message==='string'&&value.http_status===undefined;
  return Number.isInteger(value.http_status)&&value.http_status>=400&&value.http_status<500&&![408,425,429].includes(value.http_status);
}

// A transport outage or an unrelated exception must never satisfy a negative
// economic/ownership/lifecycle case merely because the caller expected failure.
export function matchesRejection(expected,actual){
  return validRejection(expected)&&object(actual)&&Object.entries(expected).every(([key,value])=>actual[key]===value);
}

function validateCases(value){
  requireThat(Array.isArray(value)&&value.length>=1&&value.length<=32,'Cases must be an array of one to 32 explicit reads or reviews.');
  const names=new Set();
  for(const row of value){
    requireThat(object(row)&&Object.keys(row).every(key=>['name','account','id','action','asset','amount','expectAction','reject'].includes(key))&&
      typeof row.name==='string'&&/^[A-Za-z0-9][A-Za-z0-9 ._-]{0,79}$/.test(row.name)&&!names.has(row.name)&&
      ADDRESS.test(row.account)&&row.account!==ZERO&&typeof row.id==='string'&&/^[1-9][0-9]{0,77}$/.test(row.id)&&BigInt(row.id)<2n**256n&&
      ['activate','increase','read'].includes(row.action)&&
      (row.reject===undefined||row.reject===false||validRejection(row.reject)),'Invalid explicit consumer case or typed rejection expectation.');
    names.add(row.name);
    if(row.action==='read'){
      requireThat(row.asset===undefined&&row.amount===undefined&&row.expectAction===undefined,'Read cases contain only public owner and NFT identity.');
    }else{
      requireThat(['ETH','ZZZ'].includes(row.asset)&&
        (row.amount===undefined||typeof row.amount==='string'&&row.amount.length<=80&&/^(0|[1-9][0-9]*)(\.[0-9]+)?$/.test(row.amount))&&
        (row.action!=='increase'||row.amount!==undefined)&&
        (row.expectAction===undefined||['approve',row.action].includes(row.expectAction)),
      'Contribution cases require ETH/ZZZ and an explicit growth amount.');
    }
  }
  return value;
}

async function websiteSources(root){
  const pending=['deployment-api.js','browser-wallet.js','package.json'],files={},messages=new Set();
  while(pending.length){
    const relative=pending.pop();if(Object.hasOwn(files,relative))continue;
    const absolute=await realpath(path.join(root,relative));
    const inside=path.relative(root,absolute);
    requireThat(inside&&!inside.startsWith('..'+path.sep)&&!path.isAbsolute(inside),'Website imports must remain inside the selected checkout.');
    const bytes=await readFile(absolute);files[relative]=sha(bytes);
    if(!relative.endsWith('.js'))continue;
    const source=bytes.toString('utf8');
    // Only exact source-authored validation messages may be recorded. Never echo
    // an unknown network/provider error or remote response body into evidence.
    for(const match of source.matchAll(/(?:fail|Error)\(\s*(['"])([^'"\r\n]{1,300})\1\s*\)/g))messages.add(match[2]);
    for(const match of source.matchAll(/^\s*(?:import\s+(?:[^;\r\n]*?\s+from\s+)?|export\s+[^;\r\n]*?\s+from\s+)['"]([^'"]+)['"]/gm)){
      requireThat(match[1].startsWith('./')||match[1].startsWith('../'),'Website consumer imports must be local source files.');
      const dependency=path.posix.normalize(path.posix.join(path.posix.dirname(relative),match[1]));
      requireThat(!dependency.startsWith('../')&&!path.posix.isAbsolute(dependency),'Website imports must remain inside the selected checkout.');
      pending.push(dependency);
    }
  }
  return {files:Object.fromEntries(Object.entries(files).sort(([a],[b])=>a.localeCompare(b))),messages};
}

function safeError(error,messages){
  const status=Number.isInteger(error?.status)&&error.status>=400&&error.status<=599?error.status:null;
  const scoped=typeof error?.message==='string'&&error.message.length<=300&&
    /^(?:A reviewed source9 runtime changed: [a-z_]+|Source9 (?:parent\/module binding differs|capability differs): [a-z_]+\.[A-Za-z0-9_(),]+|Source9 returned malformed [A-Za-z0-9_(),]+|Chain RPC could not complete eth_[A-Za-z]+)$/.test(error.message);
  const safe=messages.has(error?.message)||scoped;
  const transport=typeof error?.message==='string'&&error.message.startsWith('Chain RPC');
  return {category:status?'http':safe&&!transport?'consumer_validation':'unavailable',
    message:safe?error.message:'The local consumer read or unsigned review was unavailable.',
    ...(status?{http_status:status}:{})};
}

async function run(options,report){
  const origin=loopback(options.origin,{origin:true});
  const root=await realpath(options['website-root']);
  requireThat((await stat(root)).isDirectory(),'Website root must be a directory.');
  const [manifestBytes,casesBytes]=await Promise.all([readFile(options.manifest),readFile(options.cases)]);
  requireThat(manifestBytes.length<=2*1024*1024&&casesBytes.length<=65536,'Reviewed input exceeds the rehearsal bound.');
  const manifest=JSON.parse(manifestBytes.toString('utf8'));
  requireThat(object(manifest)&&manifest.schema===4&&manifest.source_profile===9&&manifest.accounting_version===7&&
    manifest.environment==='rehearsal','An explicit schema4/source9/accounting7 rehearsal manifest is required.');
  const rpcURL=loopback(manifest.rpc_url),cases=validateCases(JSON.parse(casesBytes.toString('utf8')));
  const source=await websiteSources(root);
  Object.assign(report,{manifest_sha256:sha(manifestBytes),cases_sha256:sha(casesBytes),
    website_source:{external_checkout:true,root,files:source.files}});
  const [{DeploymentAPI},{createChainReader}]=await Promise.all([
    import(pathToFileURL(path.join(root,'deployment-api.js')).href),
    import(pathToFileURL(path.join(root,'browser-wallet.js')).href)]);
  const rpcMethods={},httpMethods={};let forbidden=false;
  const actualFetch=globalThis.fetch;
  requireThat(typeof actualFetch==='function','This runner requires Node with native fetch.');
  const fetcher=async(url,init={})=>{
    const target=new URL(url);
    if(target.href===rpcURL){
      let request;
      try{request=JSON.parse(init.body);}catch{forbidden=true;throw Error('The consumer attempted a forbidden RPC operation.');}
      const params=Array.isArray(request?.params)?request.params:null;
      const pinned=object(params?.[1])&&Object.keys(params[1]).sort().join()==='blockHash,requireCanonical'&&
        /^0x[0-9a-f]{64}$/.test(params[1].blockHash)&&params[1].requireCanonical===true;
      const stateRead=['eth_call','eth_estimateGas','eth_getBalance','eth_getCode'].includes(request?.method);
      const shape=params&&(stateRead?params.length===2&&pinned:request?.method==='eth_getBlockByNumber'?
        params.length===2&&/^0x(?:0|[1-9a-f][0-9a-f]*)$/.test(params[0])&&params[1]===false:params.length===0);
      if(init.method!=='POST'||!object(request)||request.jsonrpc!=='2.0'||!RPC_READS.has(request.method)||!Array.isArray(request.params)||!shape){
        forbidden=true;throw Error('The consumer attempted a forbidden RPC operation.');
      }
      rpcMethods[request.method]=(rpcMethods[request.method]||0)+1;
    }else{
      const suffix=target.pathname.slice(manifest.api_prefix.length),method=init.method||'GET';
      if(target.origin!==origin||target.username||target.password||target.search||target.hash||!target.pathname.startsWith(manifest.api_prefix)||
        !(method==='GET'&&(suffix==='/v1/protocol'||/^\/v1\/nfts\/[1-9][0-9]{0,77}$/.test(suffix))||
          method==='POST'&&suffix==='/v1/activation/prepare')){
        forbidden=true;throw Error('The consumer attempted an unexpected HTTP operation.');
      }
      const key=method+' '+suffix;httpMethods[key]=(httpMethods[key]||0)+1;
    }
    return actualFetch(url,init);
  };
  const api=new DeploymentAPI(manifest,{origin,fetcher,reader:createChainReader(rpcURL,{fetcher})});
  for(const selected of cases){
    const expected=object(selected.reject)?selected.reject:null;
    const result={name:selected.name,selected_input:{...selected},expected_rejection:expected!==null,
      ...(expected?{rejection_expectation:{...expected}}:{}),passed:false,signing_enabled:false};
    const beforeRPC={...rpcMethods},beforeHTTP={...httpMethods};let stage='read_protocol';
    try{
      if(selected.action==='read'){
        result.intent={action:'read',account:selected.account,id:selected.id};
        result.protocol=await api.protocol();stage='read_nft';
        result.nft=await api.nft(selected.id,selected.account);
      }else{
        let amount=selected.amount;
        if(amount===undefined){stage='activation_quote';result.quote=await api.activationAmount(selected.asset);amount=result.quote.amount;}
        result.intent={action:selected.action,account:selected.account,id:selected.id,asset:selected.asset,amount};
        stage='prepare';result.draft=await api.prepare(result.intent);
        stage='verify_review';
        requireThat(result.draft.signing_enabled===false&&result.draft.transaction&&
          !Object.hasOwn(result.draft.transaction,'nonce'),'The source9 review must remain unsigned without a nonce.');
        requireThat(selected.expectAction===undefined||result.draft.action===selected.expectAction,'Returned review action differs from the explicit expectation.');
      }
      result.outcome='accepted';result.passed=expected===null;
      if(!result.passed)result.error={category:'unexpected_success',message:'The expected rejection did not occur.'};
    }catch(error){
      result.outcome='rejected';result.error={stage,...safeError(error,source.messages)};
      result.passed=expected!==null&&!forbidden&&matchesRejection(expected,result.error);
      if(expected)result.rejection_matched=result.passed;
    }
    result.rpc_method_counts=Object.fromEntries(Object.entries(rpcMethods).map(([method,count])=>[method,count-(beforeRPC[method]||0)]).filter(([,count])=>count));
    result.http_method_counts=Object.fromEntries(Object.entries(httpMethods).map(([method,count])=>[method,count-(beforeHTTP[method]||0)]).filter(([,count])=>count));
    if(expected&&result.passed&&(!Object.keys(result.rpc_method_counts).length||!Object.keys(result.http_method_counts).length)){
      result.passed=false;result.rejection_matched=false;
    }
    report.cases.push(result);
  }
  const finalSource=await websiteSources(root);
  report.website_source.unchanged_during_run=JSON.stringify(source.files)===JSON.stringify(finalSource.files);
  report.rpc_method_counts=rpcMethods;report.http_method_counts=httpMethods;
  report.actual_http_rpc=Object.keys(rpcMethods).length>0&&Object.keys(httpMethods).length>0;
  report.forbidden_operation_attempted=forbidden;
  report.passed=!forbidden&&report.website_source.unchanged_during_run&&report.cases.every(result=>result.passed);
}

async function main(){
  let options;
  try{options=argumentsOf(process.argv.slice(2));}catch{process.stderr.write(usage+'\n');return 2;}
  if(options===null){process.stdout.write(usage+'\n');return 0;}
  let output;
  try{output=await open(options.output,'wx');}catch{process.stderr.write('Evidence output must be a new writable file.\n');return 2;}
  const report={schema:1,kind:'source9_actual_consumer_rehearsal',started_at:new Date().toISOString(),
    actual_http_rpc:false,actual_clock:true,signing_enabled:false,transactions_submitted:0,
    production_approved:false,node_version:process.version,runner_sha256:sha(await readFile(fileURLToPath(import.meta.url))),cases:[],passed:false};
  try{await run(options,report);}catch{report.error={category:'preflight_or_runner',message:'The reviewed local inputs or consumer execution could not be admitted.'};}
  report.finished_at=new Date().toISOString();
  try{await output.writeFile(JSON.stringify(report,null,2)+'\n');}finally{await output.close();}
  process.stdout.write(report.passed?'Source9 consumer evidence passed.\n':'Source9 consumer evidence retained a failure.\n');
  return report.passed?0:1;
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  try{process.exitCode=await main();}catch{process.stderr.write('Consumer rehearsal failed; retain its exclusive evidence file.\n');process.exitCode=1;}
}
