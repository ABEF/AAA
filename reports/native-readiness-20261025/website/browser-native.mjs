import {readFile,writeFile} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
import {nativeSetup} from './staged-site/tests/helpers/deployment-native-fixture.mjs';
const staged=new URL('./staged-site/',import.meta.url),out=new URL('./',import.meta.url);
const site='C:/Users/Ali/Desktop/2.x holas/Oto/aaa-website';
const {chromium}=createRequire('C:/Users/Ali/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/')('playwright');
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const records=[];
try{
  for(const name of ['activate_eth','increase_eth','approve_usdg','claim_eth_both']){
    const s=nativeSetup(name),origin='http://127.0.0.1:47867';
    // An HTTPS read endpoint keeps this browser harness in unsigned-review mode.
    // Every network response below is a fixture; no endpoint is contacted.
    s.m.rpc_url='https://native-fixture.invalid/';
    const context=await browser.newContext({viewport:{width:1440,height:1100}}),page=await context.newPage(),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.addInitScript(({owner})=>{
      Date.now=()=>1000000;window.__methods=[];
      window.ethereum={request:async({method})=>{window.__methods.push(method);if(['eth_accounts','eth_requestAccounts'].includes(method))return [owner];throw Error('Unexpected wallet request '+method);},on(){},removeListener(){}};
    },{owner:s.f.nft.owner});
    await page.route('https://native-fixture.invalid/**',async route=>{
      const request=route.request().postDataJSON(),result=await s.reader.request(request);
      await route.fulfill({contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify({jsonrpc:'2.0',id:request.id,result})});
    });
    await page.route(origin+'/**',async route=>{
      const path=new URL(route.request().url()).pathname;
      if(path==='/deployment-config.js')return route.fulfill({contentType:'text/javascript',body:'export const DEPLOYMENT='+JSON.stringify(s.m)+';'});
      if(path.startsWith('/api/v1/')){
        let dto,status=200;
        if(path.endsWith('/protocol'))dto=s.f.protocol;
        else if(path.endsWith('/mint-readiness'))dto={schema:2,chain_id:31337,nft:s.pins.nft,minted:1,new_minting_stopped:false,provenance:s.f.nft.provenance};
        else if(path.endsWith('/prepare'))dto=s.f.draft;
        else if(path.endsWith('/nfts')&&path.includes('/wallets/'))dto={schema:2,chain_id:31337,available:true,wallet:s.f.nft.owner,nft_contract:s.pins.nft,count:1,token_ids:[s.f.nft.token_id],provenance:s.f.nft.provenance};
        else if(path==='/api/v1/nfts/'+s.f.nft.token_id)dto=s.f.nft;
        else{status=404;dto={error:'Optional history/summary is not configured in this isolated UI fixture'};}
        return route.fulfill({status,contentType:'application/json',body:JSON.stringify(dto)});
      }
      const name=path==='/'?'index.html':decodeURIComponent(path.slice(1));
      if(!/^[A-Za-z0-9_./-]+$/.test(name)||name.split('/').includes('..')||name.startsWith('.'))return route.abort();
      let body;try{body=await readFile(new URL(name,staged));}catch{body=await readFile(resolve(site,name));}
      const type={'.js':'text/javascript','.html':'text/html','.css':'text/css','.json':'application/json','.jpg':'image/jpeg','.png':'image/png','.svg':'image/svg+xml','.mp4':'video/mp4'}[extname(name)]||'application/octet-stream';
      return route.fulfill({body,contentType:type});
    });
    await page.goto(origin+'/#my-nfts');
    await page.locator('.header-actions [data-connect]').click();
    await page.locator('[data-deployment-provider]').click();
    await page.locator('#owned-nfts .nft-card').waitFor();
    await page.waitForFunction(()=>!document.querySelector('#mint-submit').disabled);
    if(name==='claim_eth_both')await page.locator('[data-deployment-claim]').click();
    else{
      await page.locator('[data-deployment-grow]').click();
      const form=page.locator('[data-deployment-contribution]');
      assert.match(await form.innerText(),/up to 2% execution loss or undeployed value/);
      if(name==='increase_eth')await form.locator('[name=amount]').fill('100');
      else await page.waitForFunction(()=>document.querySelector('[data-deployment-contribution] [name=amount]')?.value==='100');
      await form.locator('[name=consent]').check();await form.locator('button[type=submit]').click();
    }
    await page.locator('.local-confirm[open]').waitFor();
    const text=await page.locator('.local-confirm').innerText();
    assert.match(text,/UNSIGNED REVIEW/);assert.match(text,/Nothing has been approved or transferred/);
    assert.equal(await page.locator('[data-deployment-send]').count(),0);
    assert.match(text,/Network gas/);
    if(name!=='claim_eth_both'){assert.match(text,/Maximum execution loss \/ undeployed value\s+2%/);assert.match(text,/Minimum added LP\s+\$98\.00/);}
    if(name==='approve_usdg')assert.match(text,/Approval alone adds no liquidity/);
    assert.deepEqual(errors,[]);
    const methods=await page.evaluate(()=>window.__methods);assert.ok(methods.every(m=>['eth_accounts','eth_requestAccounts'].includes(m)));
    records.push({case:name,passed:true,wallet_methods:methods,rpc_calls:s.calls.filter(c=>c.method).length});
    await context.close();
  }
  await writeFile(new URL('browser-results.json',out),JSON.stringify({scope:'Actual headless DOM/modules, current Python protocol/NFT/preparation DTOs over synthetic dependencies; explicit synthetic inventory/readiness and unavailable optional history; no extension, chain, public network or send',records},null,2)+'\n');
  console.log(JSON.stringify(records));
}finally{await browser.close();}
