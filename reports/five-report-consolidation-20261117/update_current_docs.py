"""Consolidate current documentation; preserve original evidence and task status."""
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OWN=Path(__file__).resolve().parent
EXTERNAL=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/five-report-consolidation-20261117')


def text(path):return (ROOT/path).read_text(encoding='utf-8')


def write(path,value,records):
    target=ROOT/path;old=target.read_bytes();new=value.encode('utf-8')
    a=old.splitlines(keepends=True);b=new.splitlines(keepends=True)
    clean=lambda rows:[row.rstrip(b'\r\n') for row in rows]
    result=[]
    for kind,i,j,k,l in SequenceMatcher(a=clean(a),b=clean(b),autojunk=True).get_opcodes():
        result.extend(a[i:j] if kind=='equal' else b[k:l])
    assert clean(result)==clean(b)
    raw=b''.join(result);target.write_bytes(raw)
    records[path]={'before_sha256':hashlib.sha256(old).hexdigest(),'after_sha256':hashlib.sha256(raw).hexdigest(),
                   'before_lines':len(a),'after_lines':len(b)}


def main():
    records={}
    original=text('README.md');body=original[original.index('## Architecture overview'):]
    intro='''# ZZZ Collection - Proof of Permanent Liquidity (PoPL)

PoPL connects transferable ERC-721 NFTs to vault-managed ETH/ZZZ liquidity.
Activation attaches an independently accounted LP share and unlocks funded LP
fees plus rarity-weighted NFT-sale royalties. Holders cannot redeem principal
during normal operation. Governance can permanently end LP activity and return
actual ETH + ZZZ to current NFT owners; transfers, old rewards and royalties remain.

**Source candidate; undeployed for production. Production NOT APPROVED.**
Current accounting7/direct Entry3/custody5/mint2 uses canonicalV10. The trusted
normal build is `seal-boundaries-20261117`. Source publication does not update
contracts, services, journals or websites; public signing remains disabled.

[Project Todo](TODO.md) | [Feature and evidence reference](docs/IMPLEMENTATION_STATUS.md) |
[Operator manual](docs/OPERATOR_MANUAL.md) | [Current findings](docs/AUDIT_FINDINGS.md) |
[Release approval](docs/RELEASE_CHECKLIST.md)

The [latest five-report consolidation](reports/five-report-consolidation-20261117/REVIEW.md)
separates corrected defects, retained policies and remaining qualification.
Original reports keep their own source stages; test counts are not added into
a new whole-project pass. Independent feeds/routes, VRF/OpenSea, exact operating
costs, current integration rollout and independent audit remain open.

'''
    write('README.md',intro+body,records)
    assert text('README.md').split('## Architecture overview',1)[1]==original.split('## Architecture overview',1)[1]
    # Keep the functional context; remove the repeated report chronology before it.
    original=text('PROJECT_CONTEXT.md');tail=original[original.index('## Current architecture and economics'):]
    tail=tail.replace('LP-routing2/pricing2/Entry3/review2/direct governance2/fee-intake1.',
        'LP-routing3/execution-price1/pricing2/Entry3/review2/direct governance2/fee-intake1; historical LP2 remains explicit.')
    tail=tail.replace('CanonicalV9 royalty header (unchanged royalty4 layout)',
        'Current canonicalV10 retains the earlier five-word royalty4 header layout; that header')
    tail=tail.replace('that header five words includes end/capacity;', 'includes end/capacity;')
    tail=tail.replace('now carried inside V9.', 'now carried inside V10 (earlier V9 evidence keeps its own source scope).')
    tail=tail.replace('Schema14 authenticates the full graph\nfrom independent final compiler pins;',
        'Current schema17 authenticates the complete matching graph; earlier schema14\nevidence retains its own source scope. Use exact reviewed compiler pins;')
    context='''# PoPL current project context

Production is undeployed and NOT APPROVED. Use the [sole Todo](TODO.md),
[current findings](docs/AUDIT_FINDINGS.md), [operator manual](docs/OPERATOR_MANUAL.md)
and [environment map](docs/SITE_ENVIRONMENTS.md). Source publication is not rollout.

The trusted build remains `seal-boundaries-20261117`. The
[five-report consolidation](reports/five-report-consolidation-20261117/REVIEW.md)
records what is resolved, retained and still unqualified. The new historical
evidence checker verifies fixed records without rerunning or adopting them;
its weaker claim-only evidence tier stays explicit. No safeguard or NFT right
changes. New pre-seal stop warnings disclose pool operations disabled separately
from deposits; complete input is still not readiness.

'''
    write('PROJECT_CONTEXT.md',context+tail,records)
    old=text('docs/WORK_HANDOFF.md');preservation=old[old.index('## Preserve actual state'):]
    table=preservation[preservation.index('| Protected tracked file |'):]
    handoff='''# Work handoff

## Current source and authority boundary

Main only. Production is undeployed and NOT APPROVED. Current trusted normal
build: `seal-boundaries-20261117`; all61 Solidity sources and financial defaults
are unchanged by the [five-report consolidation](../reports/five-report-consolidation-20261117/REVIEW.md).
Use [current context](../PROJECT_CONTEXT.md), the [sole Todo](../TODO.md),
[feature reference](IMPLEMENTATION_STATUS.md) and [operator manual](OPERATOR_MANUAL.md).
Historical artifacts/runtimes/checkpoints/journals retain their original profiles.

## Latest completed work

- Consolidated five root report families selected by Git publication history,
  with original300files/37Markdown files preserved. The
  [finding registry](../reports/five-report-consolidation-20261117/RECONCILIATION.json)
  separates resolved defects, retained policies, structural/evidence limits and
  external qualification. Do not sum overlapping old tests into current coverage.
- Pre-seal output now names each pool with ordinary operations disabled.
  Contributions, compound and ordinary rebalance can be stopped while harvesting
  and earned claims retain their separate guards. No configuration is changed.
- A fixed historical-evidence checker binds exact method IDs, results and
  available artifacts/source metadata. Claim-only records stay visibly weaker.
  Integrity does not prove original execution, new-source behavior or release.
- Earlier manual final-anchor, frozen-gas, artwork/chain/reservation and test
  repairs remain implemented. Follow [before-sealing boundaries](SEAL_READINESS.md).

## Next work and required inputs

1. Qualify actual independent ETH/ZZZ prices, usable forward/reverse routes,
   provider capacity and complete fees; retain every existing financial guard.
2. Review real governance/keeper/guardian/payee, immutable module/dependency,
   SeaDrop/VRF and artwork inputs. Unknown inputs stay blocked. No public
   deployment or sealing is authorized by a complete offline review.
3. Qualify selected maximum currency/claim/position workloads and real operator
   recovery. Preserve existing queues/journals and reconcile pending work first.
4. Roll out matching services/site only after separate authorization and exact
   runtime/configuration review. Obtain independent audit/remediation and release
   approval. Current simulation/integration sites are not production sign-off.

## Maintenance checks

```text
python scripts/generate-function-reference.py --check
python scripts/generate-operator-reference.py --check
python scripts/sync-project-todo.py --check
python scripts/check-focused-evidence.py
python scripts/check-python-publication.py --index
```

Repeat the last check against committed HEAD. The evidence command only admits
its reviewed historical baseline; it runs no tests, compiler, RPC or signing.
Use new/affected checks for source changes and keep failed/empty/skipped stages.
Actual cold/target gas, current provider honesty and full-suite behavior remain
separate from static imports, reference tables and local selected observations.

## Preserve actual state

Keep Anvil8902, all NFTs/LP/balances, dist overlays and pending/nonce/receipt/spend
journals untouched. Popldemo is simulation; separately served poplint current3
is not the fresh source10/mint2 consumer. Public DEPLOYMENT stays null, shared
browser signing Anvil-only, staging heartbeat user-paused. No service/site,
existing-chain reset, signing or public transaction follows source publication.
Contract wallets need their own reviewed execution envelope; do not change
governance or weaken guards just to use the direct-EOA unsigned preparer.

Original documentation backups and new bounded observations are under:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/five-report-consolidation-20261117`.
Earlier report bytes remain in Git and the [report map](../reports/README.md).
Preserve all unrelated untracked drafts and these four tracked dirty files;
never stage them as part of this work.

'''
    write('docs/WORK_HANDOFF.md',handoff+table,records)
    # Current findings should not point to the superseded16November index.
    original=text('docs/AUDIT_FINDINGS.md')
    layer=original.split('## Current conclusions by project layer',1)[1].split('## Historical findings corrected by later work',1)[0]
    findings='''# Consolidated audit findings and evidence

The [current five-report registry](../reports/five-report-consolidation-20261117/RECONCILIATION.json)
reconciles64 distinct issues/obligations against current source. It preserves
duplicate origins and distinguishes37 resolved original subfindings,9 retained
policies,7 structural limits,2 historical-evidence limits,7 qualification buckets
and2 new corrections. These categories are not test totals or release
approvals. The [sole Todo](../TODO.md) owns project task status.

## Five reports reconciled

| Original report | Current interpretation |
| --- | --- |
| [Repaired-test impact](../reports/test-impact-followup-20261117/REVIEW.md) | Manual late-reorg handling and stale test expectations corrected; finite29method evidence retains its stages. |
| [Test/seal review](../reports/test-seal-deep-review-20261117/REVIEW.md) | Chain, artwork scheme and reservation identities fixed; all59cited methods assessed. Static inventories and finite80checks are not a full-suite pass. |
| [Behavior follow-up](../reports/operator-behavior-followup-20261117/REVIEW.md) | Empty artwork sealing and keeper clock lag fixed; extra compound waiting remains software-only by explicit decision. |
| [Operator-input audit](../reports/operator-input-audit-20261116/REVIEW.md) | Frozen gas, occupied output handling and nested inputs/units/examples corrected; source catalogue is not dynamic coverage. |
| [Pre-seal planner](../reports/preseal-planner-20261116/REVIEW.md) | Twelve typed setup families implemented; unknown inputs/identities remain unverified and no sealing/signing is added. |

Selection follows first Git publication, not filesystem dates. All300 original
files remain unchanged. See [scope and preservation](../reports/five-report-consolidation-20261117/SCOPE.json).

## New improvements from reconciliation

- Complete pre-seal input can intentionally disable ordinary pool operations.
  Output now identifies each such pool and the contribution/compound/rebalance
  stop. It does not conflate that setting with harvesting, claims or unknown data.
- [Focused evidence admission](../scripts/check-focused-evidence.py) verifies
  fixed historical method identities/results and available artifact metadata,
  rather than admitting successful counts alone. Its input-audit claim-only
  record is explicitly weaker; no missing raw log is manufactured. This check
  proves integrity at its stated tier, not execution or independent audit.
- Current README/context/handoff/feature guidance no longer bury the actual
  project behind repeated report chronology. Historical detail stays in reports.

## What remains a deliberate policy or real limit

Extra compound waiting is keeper software policy; cumulative maintenance-loss
caps were declined; emergency governance may explicitly omit financial guards.
Those are retained choices, not silently reopened requirements. Recovery of
unallocated royalties uses active weights at inclusion. Immutable identity,
pending randomness, failed-token/receiver delivery and coupled terminal payout
limits need their documented procedures or a separate consequential redesign.

Fresh independent sources/routes, authorities, supported VRF/OpenSea/artwork,
complete fees/gas, maximum state, hosting/recovery, matching integration rollout
and independent audit remain qualification work. Unknown inputs are not a code
defect and documentation never supplies approval.

## Current conclusions by project layer'''
    history='''## Earlier history and source boundaries

This five-report review does not reopen every older finding. Use the
[full-history reconciliation](../reports/full-history-reconciliation-20261104/REVIEW.md),
[remaining271 assessments](../reports/remaining-271-20261111/REVIEW.md),
[prior five-audit index](../reports/five-audit-reconciliation-20261116/FINDINGS.json)
and [report map](../reports/README.md) for older origins and exact evidence.
No old runtime, codec, claim/checkpoint, source stage or journal is relabelled.
Missing data remains unavailable, never guessed zero or substituted demo data.
'''
    write('docs/AUDIT_FINDINGS.md',findings+layer+history,records)
    original=text('docs/IMPLEMENTATION_STATUS.md');tail=original[original.index('## Current profile'):]
    head='''# Feature and evidence reference

Implementation, finite verification, installed operation and approved release
are separate milestones. Use the [sole Todo](../TODO.md),
[current findings](AUDIT_FINDINGS.md), [operator manual](OPERATOR_MANUAL.md)
and [latest consolidation](../reports/five-report-consolidation-20261117/REVIEW.md).
The trusted build remains `seal-boundaries-20261117`; current source is
undeployed for production and NOT APPROVED. No site/service adoption is implied.

'''
    start=tail.index('## Latest audit consolidation');end=tail.index('## Current evidence and limits')
    latest='''## Latest audit consolidation

The [five latest reports](../reports/five-report-consolidation-20261117/REVIEW.md)
are reconciled against current code with distinct dispositions and duplicate
origins. Chain/root/reservation guards, keeper timing, exact manual gas/anchors,
typed input descriptions and repaired economic tests remain implemented.
New pre-seal stop warnings and fixed historical-evidence admission improve
operating diagnostics and verification without changing financial contracts.

All61 Solidity sources, safeguards and defaults remain unchanged by this
consolidation. Independent markets/providers, actual OpenSea/VRF/content,
maximum workloads, deployment/operating acceptance and independent audit stay open.
Historical evidence below retains its original source, not current approval.

'''
    tail=tail[:start]+latest+tail[end:]
    tail=tail.replace('## Current evidence and limits','## Historical evidence and limits',1).replace('[Current 24-hour audit]','[November5 audit]',1)
    write('docs/IMPLEMENTATION_STATUS.md',head+tail,records)
    original=text('AGENTS.md');intro=original.split('\n\n',2)[1]
    update=('The [latest five-report consolidation](reports/five-report-consolidation-20261117/REVIEW.md) '
            'separates resolved defects, retained policy and unqualified work without relabelling original reports. '
            'Current pre-seal output discloses pool-specific ordinary-operation stops; the fixed historical evidence checker preserves exact methods and weaker evidence tiers. '
            'All61 Solidity sources, financial limits/rights and live environments remain unchanged. '
            'Trusted build remains seal-boundaries-20261117; no release approval or rollout is implied.')
    write('AGENTS.md',original.replace(intro,update,1),records)
    # Add the new diagnostics and the limits of evidence admission to procedures.
    p='docs/PRESEAL_CONFIGURATION.md'
    if p not in json.loads((OWN/'SCOPE.json').read_text())['original_doc_sha256']:
        before=(ROOT/p).read_bytes();save=EXTERNAL/'docs-before'/p;save.parent.mkdir(parents=True,exist_ok=True);save.write_bytes(before)
        scope=json.loads((OWN/'SCOPE.json').read_text());scope['original_doc_sha256'][p]=hashlib.sha256(before).hexdigest()
        (OWN/'SCOPE.json').write_text(json.dumps(scope,indent=2)+'\n',encoding='utf-8')
    value=text(p).replace('conversion disabled, maximum observation gap0, or no contribution destination.',
        'conversion disabled, maximum observation gap0, no contribution destination,\nor a pool with `operationsEnabled=false`. The latter names its exact pool ID\nand stops contributions, compound and ordinary rebalance there; it does not\nclaim harvesting or earned-reward claims are disabled by that flag alone.')
    write(p,value,records)
    p='docs/OPERATOR_MANUAL.md';value=text(p).replace('Empty venues, converterOFF, maximumGap0 |','Empty venues, converterOFF, maximumGap0, per-pool operationsOFF |',1)
    marker='## Prepare typed unsigned manual LP operations'
    addition='''## Inspect consolidated findings and historical evidence

Use [current findings](AUDIT_FINDINGS.md) to distinguish code corrections,
retained policy and actual release qualification. `python scripts/check-focused-evidence.py`
only checks its pinned historical records and exact method identities. A weaker
claim-only evidence tier stays weaker. It runs no test, RPC, compiler or wallet
action, and neither generates an operation `reviewHash` nor approves sealing.
Use the applicable current preparation procedure for actual function inputs.

'''
    assert marker in value;write(p,value.replace(marker,addition+marker,1),records)
    p='docs/DEVELOPMENT.md';value=text(p);marker='For current native financial fixtures, keep their execution interfaces current'
    addition='''For bounded historical-record integrity, run
`python3 scripts/check-focused-evidence.py`. Its code-pinned manifest admits
seven selected groups at their original source stages; the claim-only group
does not acquire a missing raw log. This executes no historical tests and does
not prove current behavior, original execution or release approval. New reviewed
baselines need explicit source/manifest review, not a caller-supplied hash.

'''
    assert marker in value;write(p,value.replace(marker,addition+marker,1),records)
    p='docs/project-todo.json';ledger=json.loads(text(p));tasks={t['id']:t for a in ledger['areas'] for t in a['tasks']}
    updates={
      'historical-findings':'The latestfive report families (publication-selected through1c18379) are reconciled into64distinct issues/obligations with duplicate origins and explicit resolved/policy/structural/evidence/qualification dispositions. All300original files remain unchanged. [Current registry](reports/five-report-consolidation-20261117/RECONCILIATION.json); no old pass count is promoted to whole-project approval.',
      'local-verification':'Fixed historical evidence admission checks exact expected method identities, Success/no-skips and trusted raw/artifact/source/selector records where available. The operator-input claim-only tier explicitly lacks an independent raw log; integrity is not execution or branch coverage. New bounded mutation checks do not rerun historical EVM/browser/suites. [Consolidation](reports/five-report-consolidation-20261117/REVIEW.md).',
      'native-production-preflight':'Complete offline pre-seal input can intentionally stop work. Explicit stop output now identifies each operationsEnabled=false pool and affected contributions/compound/ordinary-rebalance paths without conflating harvesting or claims. Configuration/calldata and false readiness remain unchanged. [Diagnostics](reports/five-report-consolidation-20261117/TOOLS_RECONCILIATION.md).',
    }
    for key,row in updates.items():assert row not in tasks[key]['acceptance'];tasks[key]['acceptance'].append(row)
    write(p,json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',records)
    p='reports/README.md';value=text(p);heading,tail=value.split('\n',1)
    intro='\n[Latest five-report consolidation](five-report-consolidation-20261117/REVIEW.md) provides the current distinct finding registry, preserved source boundaries, new pre-seal stop diagnostics and bounded historical-evidence admission. No past test totals are added into new coverage.\n'
    write(p,heading+'\n'+intro+tail,records)
    p='.gitattributes';value=text(p)
    write(p,value+'\n# Preserve exact five-report reconciliation and original diagnostics.\nreports/five-report-consolidation-20261117/** -text whitespace=cr-at-eol,-blank-at-eol,-blank-at-eof\n',records)
    (OWN/'DOC_CHANGES.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'documents_reconciled':len(records),'lines_before':sum(r['before_lines'] for r in records.values()),
                      'lines_after':sum(r['after_lines'] for r in records.values())}))


if __name__=='__main__':main()
