from pathlib import Path
R=Path.cwd();E=Path(__file__).parent
def change(name,pairs):
 p=R/name;raw=p.read_bytes();s=raw.decode().replace('\r\n','\n')
 original=E/'original-docs'/name;original.parent.mkdir(parents=True,exist_ok=True)
 if not original.exists():original.write_bytes(raw)
 for old,new in pairs:
  assert s.count(old)==1,(name,old[:80],s.count(old));s=s.replace(old,new)
 p.write_bytes(s.replace('\n','\r\n').encode()if b'\r\n'in raw else s.encode())
top='''[Checkpoint2 and manual LP preparation]({prefix}reports/checkpoint2-manual-20261107/REVIEW.md)
add exact raw-tree earnings snapshots and typed unsigned Active-state B/C/D
management reviews. Formats1/2 stay explicit; a complete raw rolling day and
operator artifact approval remain required. Manual reviews preserve caller inputs,
allow healthy market changes through a second exact simulation, and reject changed
custody/governed controls. They never sign, send, choose floors, force a fallback
or alter a journal. No Solidity/runtime/profile, service/site/Anvil/signing change.
Actual providers, wallet execution, host/lineage/archive qualification stay open.

'''
for name,prefix in [('AGENTS.md',''),('PROJECT_CONTEXT.md',''),('docs/WORK_HANDOFF.md','../')]:
 p=R/name;first=p.read_text(encoding='utf-8').splitlines()[0]
 change(name,[(first+'\n\n',first+'\n\n'+top.format(prefix=prefix))])
change('AGENTS.md',[(
 '- [Checkpoint1](docs/EARNINGS_CHECKPOINTS.md) is opt-in fresh accounting6/custody5/\n  fee-intake1, without predecessors, for earnings endpoints only.',
 '- [Checkpoint1/2](docs/EARNINGS_CHECKPOINTS.md) explicitly serve accounting6 or\n  accounting7/LP-allocation1 respectively, each custody5/fee-intake1 without\n  predecessors, for earnings endpoints only.'),(
 '  scaled NFT fractions, dust/cohorts, ownership/claims/conversions and today prices.',
 '  historical scaled NFT fractions or fresh whole units/raw tree phase, dust/cohorts,\n  ownership/claims/conversions and today prices.'),(
 '- Current evidence: final24new cases, broader147affected at its recorded earlier\n  source stage. Do not sum overlaps.',
 '- Historical checkpoint1 evidence retains24new and earlier147affected cases at\n  its original source stage. Current checkpoint2/manual source evidence is linked\n  above; do not sum overlapping stages.')])
change('README.md',[(
 '## Project navigation\n',
 'The [new backend tools](reports/checkpoint2-manual-20261107/REVIEW.md) add reviewed\nexact-unit earnings checkpoints and typed unsigned manual LP preparation. They\nchange no contract/runtime, operating service, website or signing boundary.\n\n## Project navigation\n')])
change('docs/RELEASE_CHECKLIST.md',[(
 'Reviewed2026-11-06. This approves one frozen release; it is not a second Todo.',
 'Reviewed2026-11-07. This records review of one frozen release; it is not a second Todo.'),(
 '## Evidence and approval boundary\n',
 'The [checkpoint2/manual milestone](../reports/checkpoint2-manual-20261107/REVIEW.md)\nadds backend source only. Exact artifact approval, original/no-lineage scope,\ncomplete raw24-hour suffix and source/anchor pins remain mandatory. Manual\nActive-state B/C/D uses explicit limits/masks and two exact full simulations;\nParked/other actions, actual provider/wallet execution and host operation remain\nunqualified. No Solidity, ABI, runtime, authority, financial right or installed\nenvironment changes, so unchanged normal/static contract evidence is reused.\n\n## Evidence and approval boundary\n')])
change('docs/ROADMAP.md',[(
 'Qualify the new explicit claim planner with actual worst-case currencies/fees,',
 'Source-only typed manual B/C/D preparation is implemented for Active buckets.\nQualify actual operator-selected floors, provider/hash support, complete fees and\nwallet execution; extend other states/actions separately. No signing or automatic\nforce/recenter fallback follows from preparation.\n\nQualify the new explicit claim planner with actual worst-case currencies/fees,')])
change('reports/README.md',[(
 '| Are LP conversion, ETH claims and gas limits consistent?',
 '| Can exact earnings use checkpoints and manual LP inputs be prepared? | [Checkpoint2/manual milestone](checkpoint2-manual-20261107/REVIEW.md), [verification](checkpoint2-manual-20261107/VERIFICATION.md) | Explicit exact raw-tree format2, bounded build/restore and full-day suffix; typed unsigned Active B/C/D with stable controls and fresh exact simulations. Backend only; no signing, runtime/service/site change or operating approval. |\n| Are LP conversion, ETH claims and gas limits consistent?')])
print('Current instructions, features and release boundaries updated; original report bytes retained')
