import {readFile,writeFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
const site='file:///C:/Users/Ali/Desktop/2.x%20holas/Oto/aaa-website/',root=new URL('./',import.meta.url);
let base=await readFile(new URL('tests/deployment-api.test.mjs',site),'utf8');
base=base.slice(0,base.indexOf('for(const name of Object.keys(fixtures))')).replaceAll("'../",`'${site}`).replace("'./fixtures/deployment-api.json'",`'${site}tests/fixtures/deployment-api.json'`);
await writeFile(new URL('api-helper.mjs',root),base);
let helper=await readFile(new URL('tests/deployment-transactions.test.mjs',site),'utf8');
helper=helper.slice(0,helper.indexOf('for(const name of [')).replace("'./deployment-api.test.mjs'","'./api-helper.mjs'").replaceAll("'../",`'${site}`).replace('function fixture(', 'export function fixture(');
await writeFile(new URL('flow-helper.mjs',root),helper);
const {fixture}=await import('./flow-helper.mjs');
const require=createRequire('C:/Users/Ali/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/'),{chromium}=require('playwright');
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'}),records=[];
try{
 for(const scenario of ['changed_nonce','nonce_gap']){
  const s=fixture('mint');s.m.rpc_url='http://127.0.0.1:57306';if(scenario==='nonce_gap')s.nonce=5n;
  let release;const gate=new Promise(resolve=>release=resolve);s.afterSend=async()=>{await gate;s.receipt=null;s.transaction.blockNumber=null;s.transaction.blockHash=null;s.transaction.transactionIndex=null;s.nonce=0n;if(scenario==='changed_nonce')s.transaction.nonce='0x5';};
  const context=await browser.newContext(),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.exposeFunction('walletRPC',async request=>({result:await s.provider.request(request)}));
  await page.addInitScript(()=>{Date.now=()=>1000000;window.ethereum={request:async r=>(await window.walletRPC(r)).result,on:()=>{},removeListener:()=>{}};});
  await page.route('**/deployment-config.js',r=>r.fulfill({contentType:'text/javascript',body:'export const DEPLOYMENT='+JSON.stringify(s.m)+';'}));
  await page.route('http://127.0.0.1:57306/**',async r=>{const q=r.request().postDataJSON();await r.fulfill({contentType:'application/json',body:JSON.stringify({jsonrpc:'2.0',id:q.id,result:await s.reader.request(q)})});});
  await page.route('**/api/v1/**',async r=>{try{const response=await s.fetcher(r.request().url(),{});await r.fulfill({status:response.status,contentType:'application/json',body:await response.text()});}catch{await r.fulfill({status:503,body:'{}'});}});
  await page.goto('http://127.0.0.1:8902/#mint');await page.locator('.header-actions [data-connect]').click();await page.locator('[data-deployment-provider]').click();
  await page.locator('#mint-consent').check();await page.locator('#mint-submit').click();await page.locator('[data-deployment-send]').click();
  await page.waitForFunction(()=>document.querySelector('[data-deployment-progress]')?.textContent==='Confirm in your selected wallet.');
  assert.equal(await page.locator('[data-deployment-send]').innerText(),'Confirm in your wallet');assert.equal(await page.locator('.local-confirm [data-deployment-close]').isEnabled(),true);
  release();const title=scenario==='changed_nonce'?'Wallet changed the transaction number':'Transaction waiting for earlier activity';
  await page.locator('.local-confirm h2').filter({hasText:title}).waitFor();assert.equal(s.sent.length,1);assert.equal(await page.locator('[data-deployment-send]').count(),0);
  for(let i=0;i<3;i++){await page.locator('.local-confirm [data-deployment-recover]').click();await page.locator('.local-confirm h2').filter({hasText:title}).waitFor();}
  assert.equal(s.sent.length,1);assert.deepEqual(errors,[]);
  await page.locator('.local-confirm [data-deployment-close]').click();assert.equal(await page.locator('.local-confirm').evaluate(e=>e.open),false);
  const journal=await page.evaluate(()=>Object.keys(localStorage).filter(k=>k.startsWith('popl-browser-pending-v1:')).map(k=>JSON.parse(localStorage[k])));assert.equal(journal.length,1);assert.ok(journal[0].hash);
  records.push({scenario,passed:true,simulated_sends:s.sent.length,recoveries:3,journal_preserved:true});await context.close();
 }
 await writeFile(new URL('browser-result.json',root),JSON.stringify({scope:'Headless Chrome with mocked wallet, node and API responses; fresh isolated browser storage. No actual transaction or user journal access.',records},null,2)+'\n');console.log('PASS: two pending-wallet browser scenarios, stage labels, Close and six recoveries without resubmission.');
}finally{await browser.close();}
