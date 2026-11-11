from pathlib import Path
import hashlib,json,sys
W=Path('C:/Users/Ali/Desktop/2.x holas/Oto/aaa-website');E=Path(__file__).resolve().parent
def write(name,text):
 p=W/name;old=p.read_bytes() if p.exists() else b''
 p.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n' if b'\r\n' in old else '\n').encode('utf-8'))
def read(name):return (W/name).read_text(encoding='utf-8-sig')
def replace(name,old,new,count=1):
 s=read(name);assert s.count(old)==count,(name,old,s.count(old));write(name,s.replace(old,new))
mode=sys.argv[1]
if mode=='prepare':
 names=['domain.js','app.js','preview-store.js','index.html','styles.css','README.md','PROJECT_CONTEXT.md','FRONTEND_STATE.md','tests/contribution-flow.test.mjs','package.json']
 original=E/'before-demo-alignment';original.mkdir()
 for name in names:
  p=original/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((W/name).read_bytes())
 (E/'demo-alignment-start.json').write_text(json.dumps({n:hashlib.sha256((W/n).read_bytes()).hexdigest() for n in names},indent=2)+'\n')
 write('tests/current-demo-policy.test.mjs',(E/'current-demo-policy.test.mjs').read_text())
 p='package.json';d=json.loads(read(p));assert 'tests/current-demo-policy.test.mjs' not in d['scripts']['test'];d['scripts']['test']+=' tests/current-demo-policy.test.mjs';write(p,json.dumps(d,indent=2)+'\n')
 print('Archived current dirty inputs and added current-policy regression before behavior changes.')
elif mode=='fix':
 replace('domain.js',"export const FUNDING_ASSETS = ['USDC','ZZZ','ETH','USDG'];", "// Historical v7 event/API vocabulary. Do not narrow it: old saved events replay here.\nexport const FUNDING_ASSETS = ['USDC','ZZZ','ETH','USDG'];\nexport const CURRENT_DEMO_POLICY = 2;\nexport const CURRENT_FUNDING_ASSETS = Object.freeze(['ETH','ZZZ']);\nexport const CURRENT_CONTRIBUTION_POOL = 'ZZZ/ETH';\nexport const CURRENT_CONTRIBUTION_LOSS_BPS = 300;")
 replace('domain.js',"export function activatePreview(collection, {id, amount, pool, fundingAsset = 'USDC'}) {", "// Retained legacy entry point, used only for unversioned historical events.\nexport function activatePreview(collection, contribution) {\n  return applyActivation(collection,contribution,POOLS);\n}\nfunction applyActivation(collection, {id, amount, pool, fundingAsset = 'USDC'}, pools) {")
 replace('domain.js',"if (!POOLS.includes(pool)) throw new Error('Choose a supported example pool.');", "if (!pools.includes(pool)) throw new Error('Choose a supported example pool.');")
 replace('domain.js',"export function increasePreview(collection, contribution) {", "function currentContribution(contribution) {\n  if (!CURRENT_FUNDING_ASSETS.includes(contribution.fundingAsset)) throw new Error('Choose ETH or ZZZ for the current example contribution.');\n  if (contribution.pool !== undefined && contribution.pool !== CURRENT_CONTRIBUTION_POOL) throw new Error('Choose the current ETH/ZZZ contribution pool.');\n  return {...contribution,pool:CURRENT_CONTRIBUTION_POOL};\n}\nexport function activateCurrentPreview(collection, contribution) {\n  return applyActivation(collection,currentContribution(contribution),[CURRENT_CONTRIBUTION_POOL]);\n}\nexport function increaseCurrentPreview(collection, contribution) {\n  return applyIncrease(collection,currentContribution(contribution),MIN_TOPUP_USD);\n}\n\nexport function increasePreview(collection, contribution) {")
 replace('domain.js',"if (event.type === 'activate') collection = activatePreview(collection,event).collection;\n      // Retain old v7 contributions; new writes must pass the current $5 floor.\n      if (event.type === 'increase') collection = applyIncrease(collection,event,0.01).collection;", "if (event.type === 'activate' || event.type === 'increase') {\n        if (event.demo_policy !== undefined && event.demo_policy !== CURRENT_DEMO_POLICY) throw new Error('Unknown demo contribution policy.');\n        const current = event.demo_policy === CURRENT_DEMO_POLICY;\n        if (event.type === 'activate') collection = (current ? activateCurrentPreview : activatePreview)(collection,event).collection;\n        // Unversioned v7 events retain old assets/pools and smaller-cent top-ups.\n        else collection = (current ? increaseCurrentPreview(collection,event) : applyIncrease(collection,event,0.01)).collection;\n      }")
 replace('preview-store.js',"activatePreview,increasePreview,fundDemoRewards", "activatePreview,increasePreview,activateCurrentPreview,increaseCurrentPreview,CURRENT_DEMO_POLICY,fundDemoRewards")
 replace('preview-store.js',"export function previewChange(collection,event) {\n  switch(event.type)", "export function previewChange(collection,event) {\n  if (['activate','increase'].includes(event.type) && event.demo_policy !== undefined && event.demo_policy !== CURRENT_DEMO_POLICY) throw new Error('Unknown demo contribution policy.');\n  const current=event.demo_policy===CURRENT_DEMO_POLICY;\n  switch(event.type)")
 replace('preview-store.js',"case 'activate': return activatePreview(collection,event);", "case 'activate': return (current?activateCurrentPreview:activatePreview)(collection,event);")
 replace('preview-store.js',"case 'increase': return increasePreview(collection,event);", "case 'increase': return (current?increaseCurrentPreview:increasePreview)(collection,event);")
 for unused in ['buildDemoCollection, ','replayEvents, ','mintPreview, ','claimPreview, ','activatePreview, ','increasePreview, ']:replace('app.js',unused,'')
 replace('app.js',"DEMO_ADDRESS, STORAGE_KEY, LEVELS", "DEMO_ADDRESS, STORAGE_KEY, CURRENT_DEMO_POLICY, CURRENT_FUNDING_ASSETS, CURRENT_CONTRIBUTION_POOL, CURRENT_CONTRIBUTION_LOSS_BPS, LEVELS")
 replace('app.js','<option value="USDC">USDC</option><option value="ZZZ">ZZZ</option><option value="ETH">ETH</option><option value="USDG">USDG</option>', '${CURRENT_FUNDING_ASSETS.map(asset=>`<option value="${asset}">${asset}</option>`).join(\'\')}')
 replace('app.js','At least 99% must become added LP;', 'At least ${100-CURRENT_CONTRIBUTION_LOSS_BPS/100}% must become added LP;')
 replace('app.js',"pool='ZZZ/WETH'",'pool=CURRENT_CONTRIBUTION_POOL')
 replace('app.js',"performPreview({type:action,id,amount,pool,fundingAsset}","performPreview({type:action,id,amount,pool,fundingAsset,demo_policy:CURRENT_DEMO_POLICY}")
 s=read('index.html');s=s.replace('ZZZ or USDC','ZZZ or ETH').replace('ZZZ OR USDC','ZZZ OR ETH').replace('ZZZ / USDC','ZZZ / ETH').replace('contribution-token usdc-token">USDC','contribution-token eth-token">ETH').replace('at least 100 USDC or $100 worth of ZZZ','at least $100 in ETH or ZZZ value').replace('at least 99% deployed','at least 97% deployed');assert 'USDC' not in s and 'USDG' not in s;write('index.html',s)
 replace('styles.css','.usdc-token{','.eth-token{')
 replace('tests/contribution-flow.test.mjs',"import {FUNDING_ASSETS} from '../domain.js';","import {CURRENT_FUNDING_ASSETS} from '../domain.js';")
 replace('tests/contribution-flow.test.mjs',"test('public selector keeps the four agreed choices with ETH representing native input',()=>{\n  assert.deepEqual([...FUNDING_ASSETS].sort(),['ETH','USDC','USDG','ZZZ']);", "test('current public selector exposes only native ETH and fixed ZZZ',()=>{\n  assert.deepEqual([...CURRENT_FUNDING_ASSETS].sort(),['ETH','ZZZ']);")
 note=('Current demo writes use explicit `demo_policy:2`: native ETH or fixed ZZZ,\none ETH/ZZZ contribution pool and a3%/97% illustrative contribution limit.\nUnversioned v7 saved events retain their original assets, pools, cent top-ups\nand LP-only claim meaning. The storage key, seed NFTs, artwork and balances are\nnot reset or relabelled. Existing local/runtime profiles and stronger signed\nceilings remain separate. Source changes do not update either served website.\n')
 for name in ['README.md','PROJECT_CONTEXT.md']:
  s=read(name);i=s.index('\n');write(name,s[:i+1]+'\n'+note+'\n'+s[i+1:])
 write('FRONTEND_STATE.md',note+'\n'+read('FRONTEND_STATE.md'))
 replace('README.md','some preserved\ndemo/legacy selectors still show USDG/USDC.', 'preserved\nhistorical local selectors still show USDG/USDC; current demo writes use ETH/ZZZ.')
 print('Aligned only current demo writes/UI; historical replay and real/local signing profiles unchanged.')
else:raise SystemExit('Unknown mode')
