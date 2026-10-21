import {createRequire} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const require=createRequire('C:/Users/Ali/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/'),{chromium}=require('playwright');
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
try{
 const context=await browser.newContext();await context.grantPermissions(['local-network-access'],{origin:'http://127.0.0.1:8902'});const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')console.log('browser:',m.text());});page.on('requestfailed',r=>console.log('request:',r.url(),r.failure()));
 const genesis='0x19df3ff29a52f43ea4c9120bcbf65ec6a3d707f90c4e6537d54274cfe3f4d439',owner='0x70997970c51812dc3a010c7d01b50e0d17dc79c8',hash='0x7df63aa0d6bf24461b7fdf1858b778c7d1e051d904a11a86ad0dd538a9400cc6',key=`popl-browser-pending-v1:0x7a69:${genesis}:${owner}`;
 const item={schema:1,status:'pending',hash,genesisHash:genesis,transaction:{from:owner,to:'0x2279b7a0a67db372996a5fab50d91eaa73d2ebe6',chainId:'0x7a69',nonce:'0x19',data:'0x21bf772d',value:'0xb1a2bc2ec50000'}};
 await page.route('http://127.0.0.1:8902/',r=>r.fulfill({contentType:'text/html',body:'<!doctype html><main>Isolated repair test</main>'}));
 await page.goto('http://127.0.0.1:8902/');await page.evaluate(({key,item})=>localStorage.setItem(key,JSON.stringify(item)),{key,item});
 const code=await readFile(new URL('local-mint-repair.mjs',import.meta.url),'utf8');await page.addScriptTag({type:'module',content:code});
 await page.locator('[data-repair-go]').waitFor();await page.locator('[data-repair-go]').click();
 await page.getByText('First clear MetaMask activity and nonce data on the local network.').waitFor();
 assert(await page.evaluate(key=>localStorage.getItem(key)!==null,key));
 await page.locator('[data-repair-ready]').check();await Promise.all([page.waitForEvent('load',{timeout:10000}),page.locator('[data-repair-go]').click()]).catch(async error=>{console.log(await page.locator('body').innerText());console.log(errors);throw error;});
 assert.equal(await page.evaluate(key=>localStorage.getItem(key),key),null);
 const archiveKey=`popl-local-abandoned-archive-v1:${genesis}:${hash}`;
 assert.equal(JSON.parse(await page.evaluate(key=>localStorage.getItem(key),archiveKey)).rawJournal,JSON.stringify(item));
 assert.deepEqual(errors,[]);
 await writeFile(new URL('repair-browser.json',import.meta.url),JSON.stringify({pass:true,scope:'Fresh isolated headless browser with synthetic journal; reads actual local manifest/RPC only. No extension or user-browser storage accessed.',checks:['Control displayed','Unchecked MetaMask attestation blocks cleanup','Exact synthetic journal archived byte-for-byte','Only synthetic pending record removed','Page reloads without error'],user_browser_step:'Still required'},null,2)+'\n');
 console.log('PASS: local recovery control, explicit checkbox, archival and reload; actual user browser unchanged.');
}finally{await browser.close();}
