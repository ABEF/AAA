from pathlib import Path
import json
R=Path.cwd();E=Path(__file__).parent
def save(p,s,raw):p.write_bytes(s.replace('\n','\r\n').encode()if b'\r\n'in raw else s.encode())
p=R/'docs/project-todo.json';raw=p.read_bytes();v=json.loads(raw);items={t['id']:t for area in v['areas']for t in area['tasks']}
t=items['financial-history']
t['text']='Fresh7 supports complete raw replay or explicit reviewed checkpoint2 retaining exact ETH/ZZZ trees, pending units/high-low phase/direct credits/ordinals and original-currency royalty4 tickets. Claims/conversions/imports are not income; a complete raw24-hour suffix remains mandatory. Historical checkpoint1 is6-only. Lineage/other consumers, raw archival/rotation/restore and actual lifetime workloads remain unqualified.'
t['acceptance']=[s.replace('Historical checkpoint1 remains6-only. Build/review explicit checkpoint2 and measure lifetime replay/archive/rotation/restore before claiming bounded long-term operation.',
 'Historical checkpoint1 remains6-only. Explicit checkpoint2 is implemented for original7/5/1/royalty4 deployments; independently approve artifacts and measure lifetime replay/archive/rotation/restore before claiming qualified long-term operation.')for s in t['acceptance']]
t['acceptance'].append('[Checkpoint2 implementation](reports/checkpoint2-manual-20261107/REVIEW.md): schema2 source/config/anchor binding, raw exact trees/rounding phase/direct credits, all-NFT owner/share/ticket/component/paid reconciliation, bounded offline build/advance and immutable per-request restores. Full-replay/suffix, actual producer frames and corruption/reorg/old-format/atomic-output controls retain separate source scopes. No predecessor support, automatic approval/pruning, service rollout or raised request limits. [Operator procedure](docs/EARNINGS_CHECKPOINTS.md).')
t=items['operation-review']
t['text']='Read-only keeper reports cover rebalance, compound and harvest. A separate typed unsigned CLI prepares Active-state guarded/forced same-main consolidation or full emergency replacement with explicit floors/masks, authenticated snapshots, fresh simulations and gas envelopes. Other states/actions and actual provider/operator qualification remain open; no signing or universal execution approval.'
for i,s in enumerate(t['acceptance']):
 if s.startswith('Remaining typed live manual-LP preparation:'):
  t['acceptance'][i]='[Typed manual-LP preparation](docs/MANUAL_LP_PREPARATION.md) implements explicit Active-state B/C/D as a bounded source-only milestone. Authenticate runtime/governance/pause/main/residual/control snapshots, prepare exact added-L versus new-L floors and custody/review commitments, retain the original expiry and exact calldata, and simulate freshly before publication. Healthy market movement is re-evaluated rather than treated as a geometry change. No automatic force, floor choice, signing, deadline extension, intent deletion or Parked-state support. Actual provider/manual rehearsal and wider adapters remain open. [Both-flow scope](reports/moving-market-flows-20261106/INPUT_MATRIX.md).'
  break
else:raise AssertionError('Missing current manual preparation acceptance')
v['reviewed']='2026-11-07'
save(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n',raw)
def replace(name,pairs):
 p=R/name;raw=p.read_bytes();s=raw.decode().replace('\r\n','\n')
 original=E/'original-docs'/name;original.parent.mkdir(parents=True,exist_ok=True)
 if not original.exists():original.write_bytes(raw)
 for old,new in pairs:
  assert s.count(old)==1,(name,old[:65],s.count(old));s=s.replace(old,new)
 save(p,s,raw)
replace('docs/IMPLEMENTATION_STATUS.md',[(
 'target gas, actual rollout and exact-unit checkpoint2 remain separate qualification work.',
 'target gas, actual rollout and checkpoint2 operating qualification remain separate work. Explicit checkpoint2 source support is described below.'),(
 '| Manual operation preparation | Source-bound current callable reference plus exact operating procedures; the historical90-entry inventory retains its original scope. Ordered named inputs, actual caller/reversal and full tuple links. Offline reviewHash helper validates strict source-bound ABI shapes and preserves exact decimal strings; no live reads, simulation, signing, transaction or readiness claim. [Operator guide](OPERATOR_MANUAL.md#prepare-and-check-an-offline-reviewhash). |',
 '| Manual operation preparation | Offline provenance helper remains separate. New bounded [typed B/C/D preparation](MANUAL_LP_PREPARATION.md) reads current Active-state authority/custody/control snapshots and prepares exact unsigned Migration inputs with fresh complete simulation and gas review. Caller floors/masks/deadline are explicit; no signing, automatic fallback or execution approval. Parked states/other actions and actual provider/operator qualification remain open. |'),(
 'Checkpoint1 remains6-only; reviewed exact-unit checkpoint2 and lineage/archive/workload qualification remain open.',
 'Checkpoint1 remains6-only; explicit checkpoint2 preserves raw exact trees/pending/phase/direct rights and a complete raw24-hour suffix. Lineage/archive/workload/operating qualification remain open.')])
replace('docs/AUDIT_FINDINGS.md',[(
 'Checkpoint1 is6-only; exact-unit checkpoint2 remains open.',
 'Checkpoint1 is6-only; explicit checkpoint2 now retains the raw whole-unit books for original7 deployments. [Checkpoint/manual follow-up](../reports/checkpoint2-manual-20261107/REVIEW.md) separates source completion from real provider/host/lineage qualification.')])
replace('docs/README.md',[(
 '| Rewards and lifetime history | [Earnings](EARNINGS_HISTORY.md),',
 '| Rewards and lifetime history | [Reviewed checkpoint1/2](EARNINGS_CHECKPOINTS.md), [Earnings](EARNINGS_HISTORY.md),'),(
 '| Management and keeper | [Operator manual](OPERATOR_MANUAL.md),',
 '| Management and keeper | [Typed unsigned manual LP preparation](MANUAL_LP_PREPARATION.md), [Operator manual](OPERATOR_MANUAL.md),')])
print('Updated financial-history and operation-review milestones; full task statuses remain in progress')
