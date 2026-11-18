"""Reconcile current guidance/Todo, retaining historical evidence and raw lines."""
from pathlib import Path
import difflib,hashlib,json

R=Path(__file__).resolve().parents[2]
O=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/activation-final-six-20261118/docs-root')
O.mkdir(parents=True,exist_ok=False)
manifest={}
def put(name,text):
    p=R/name;raw=p.read_bytes();(O/name).parent.mkdir(parents=True,exist_ok=True);(O/name).write_bytes(raw)
    old=raw.decode('utf-8').splitlines(True);new=text.replace('\r\n','\n').splitlines(True)
    a=[x.rstrip('\r\n')for x in old];b=[x.rstrip('\r\n')for x in new];out=[]
    for tag,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():
        out.extend(old[i:j]if tag=='equal'else new[k:l])
    updated=''.join(out).encode('utf-8');p.write_bytes(updated)
    manifest[name]={'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':hashlib.sha256(updated).hexdigest(),'unchanged_line_bytes_preserved':True}

for name in ('AGENTS.md','PROJECT_CONTEXT.md','docs/WORK_HANDOFF.md','docs/ROADMAP.md','docs/RELEASE_CHECKLIST.md'):
    p=R/name;text=p.read_text(encoding='utf-8')
    start=text.index('The current trusted normal build is `activation-gas-20261118`.')
    end=text.index('\n\n',start)
    link=(''if '/'not in name else'../')+'reports/activation-final-six-20261118/REVIEW.md'
    paragraph=(f'The current trusted normal build is `activation-final-six-20261118`, with explicit Factory6/allocation2. '
        f'The [activation review]({link}) closes all six previous refusals: all13 controlled cold cases fit20M with full20% padding and pass their financial checks. '
        'Worst gas is16,460,899 raw/19,753,079 padded. The closed100-source graph passes48 unchanged normal gates. '
        'Exact LP/royalty entitlements, all safeguards,12M default and existing environments remain unchanged. '
        'Fresh private codecs and transaction-only Pricing require exact new source/runtime pins; never copy old physical storage or relabel payload5/journals. '
        'Actual markets, selected currencies/providers/complete fees,64-currency/two-LP/all-order workloads, operating acceptance and independent approval remain open. '
        'The six measured cases are resolved; broad Q03 and release qualification remain open.')
    text=text[:start]+paragraph+text[end:]
    if name=='AGENTS.md':text=text.replace('Reviewed2026-11-17.','Reviewed2026-11-18.')
    put(name,text)

name='docs/POSITION_V7.md';text=(R/name).read_text(encoding='utf-8')
old='The fresh `activation-gas-20261118` build preserves public accounting7/LP-allocation1/schema17/canonicalV10 records'
start=text.index(old);end=text.index('\n',start)
text=text[:start]+('The fresh `activation-final-six-20261118` / payload6 build preserves public accounting7/LP-allocation1/schema17/canonicalV10 logical records. '
    'LP phase uses a MAX128 sentinel/full-width spill; Royalty status and Book coefficients use new private encodings without narrowing money or lifetime coefficients. '
    'Pricing basis/marks/list are transaction-scoped and explicitly cleared after each atomic operation. Public selectors/types/rights remain; three getter address-input names become `asset`. '
    'Use fresh exact source/runtime/data pins and logical canonical import, never old raw slots or relabelled snapshots/journals. '
    'The [current verification](../reports/activation-final-six-20261118/REVIEW.md) qualifies all13 controlled cold cases within20M/full20%; real markets/providers/fees and wider workloads remain separate.')+text[end:]
put(name,text)

name='docs/DEVELOPMENT.md';text=(R/name).read_text(encoding='utf-8')
needle='| ActivationExecutionBoundary20261118 / activation-gas source-scoped components |'
start=text.index(needle);end=text.index('\n',start)
text=text[:start]+('| Activation final-six source-scoped components | Fresh Oracle codecs, transaction-only Pricing, feed identity, LP sentinel and Royalty status/Book checks are preserved with exact sources in [the engineering archive](../reports/activation-final-six-20261118/engineering/MANIFEST.json). Two affected actual Rewards canonical methods and one affected existing1,000-NFT producer re-execute for six changed source files;13 cold cases all fit20M/full20%. Frozen controls stay unchanged. New F6 Python controls are discovered by the maintained Python runner; historical loader controls use explicit archives. No unchanged full suite is claimed. |')+text[end:]
put(name,text)

p=R/'docs/project-todo.json';value=json.loads(p.read_bytes())
intro='[Current six-case gas resolution](reports/activation-final-six-20261118/REVIEW.md): '
updates={
 'royalty-eth-settlement':'Payload6 packs status and exact Book coefficients with full-width spill, preserving original currencies, one-hour/fault cohorts, current-owner rights and flatV10 rows. All13 controlled cold scenarios pass20M/full20%; real selected-currency and wider-workload qualification remains open. Historical payload5 is not relabelled.',
 'activation-assets':'All six previous cold activation refusals close; all13 matched ETH/ZZZ activation/growth cases pass financial checks and20M/full20%. Worst16,460,899raw/19,753,079padded. Controlled depth/feeds/currencies do not qualify actual routes/prices/provider fees or64-currency/two-leg/every-order state.',
 'royalty-reporting':'Public royalty events/reporting5 and canonicalV10 logical rows remain exact under fresh private F6/LP carry codecs. Two affected actual Rewards/immutable-Canonical methods preserve2029logical rows and backing/owner/future-income cycles. Never reinterpret old raw storage/checkpoints or relabel old runtimes.',
 'activation-quotes':'The exact1000-NFT producer plus13coldchecks preserves entrant-only placement, actual marginal LP, source/callback and loss guards. All13 now fit20M with full20%; all six previous refusals close. Exact fresh estimation/padded simulation remains mandatory; no default/cap/read allowance is raised.',
 'native-production-preflight':'The current registry authenticates100closed sources/48normal gates under activation-final-six-20261118 and explicit F6. Exact older F5 remains archived; unknown inputs/addresses/observations and all approvals stay blocked/unverified. Current thirteen cold passes are controlled evidence, not constructor/provider/market/deployment acceptance.',
 'local-verification':'One affected existing1,000-NFT method exports13coldcases; every financial check and20M/full20% call passes. LP/royalty/price-context component and canonical/consumer checks retain distinct source scopes; unchanged old suites are not rerun. Full normal source admission and rejected/tool/fixture stages remain explicit.',
 'deployment-initcode':'Fresh F6 creation/data/code pins and changed hosts require new reviewed construction.100-source/48normal gates pass; Royalty24562/14, Oracle23406/1170, Rewards23983/593runtime bytes/headroom; Accessfullinit48580. No old constructor receipt is relabelled and no deployment/seal is authorized.',
}
seen=set()
for area in value['areas']:
    for task in area['tasks']:
        if task['id']in updates:
            acceptance=task['acceptance'];count=0
            for i,line in enumerate(acceptance):
                if line.startswith('[Current activation-gas work]'):
                    acceptance[i]=intro+updates[task['id']];count+=1
            assert count==1,(task['id'],count);seen.add(task['id'])
        if task['id']=='deployment-initcode':
            task['acceptance'].append('Editorial follow-up at the next source revision: correct the inline Royalty status sketch (actual16/16/16 bits, initial bit48), then regenerate fresh source/artifact pins. Current reviewed getters/layout and operator guidance are correct; this is not a financial or gas blocker. Keep the frozen qualified source unchanged for a comment-only edit.')
assert seen==set(updates)
testing=next(a for a in value['areas']if a['id']=='testing')
assert not any(t['id']=='activation-gas-six-cases'for a in value['areas']for t in a['tasks'])
testing['tasks'].insert(1,{'id':'activation-gas-six-cases','status':'done',
 'title':'Fit the six remaining activation cases into20M',
 'text':'All13 controlled near1000-NFT cold scenarios, including all six earlier refusals, now pass exact accounting and20M with full20% headroom. Worst padded19,753,079; limits and entitlements unchanged.',
 'href':'reports/activation-final-six-20261118/REVIEW.md',
 'acceptance':['Same thirteen complete calls, sender/calldata/value and controlled market anchor are compared against the exact earlier baseline; all estimates decrease. Every admitted padded call actually succeeds on an owned fresh loopback node.',
 'One affected existing producer, exact component/canonical/consumer checks and100-source/48-gate normal admission retain their separate scopes. Old suites/reports/private states and live environments are preserved.',
 'This finite milestone does not close broad Q03: actual selected assets/prices/routes/provider/fees,64-currency/two-LP/every-order maximum workloads and independent release approval remain required.']})
value['reviewed']='2026-11-18'
put('docs/project-todo.json',json.dumps(value,indent=2,ensure_ascii=False)+'\n')
(O/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('Updated',len(manifest),'current documents/ledger; retained historical scopes and unchanged raw lines.')
