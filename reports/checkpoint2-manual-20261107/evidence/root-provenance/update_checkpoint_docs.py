from pathlib import Path
R=Path.cwd();E=Path(__file__).parent
def edit(name,changes):
 p=R/name;raw=p.read_bytes();s=raw.decode().replace('\r\n','\n')
 original=E/'original-docs'/name
 original.parent.mkdir(parents=True,exist_ok=True)
 if not original.exists():original.write_bytes(raw)
 for old,new in changes:
  assert s.count(old)==1,(name,old[:90],s.count(old));s=s.replace(old,new)
 p.write_bytes(s.replace('\n','\r\n').encode()if b'\r\n'in raw else s.encode())
edit('docs/EARNINGS_HISTORY.md',[(
 'Full raw history is required on7; checkpoint1 is rejected before restoring state.\nExact-LP checkpoint2 remains open for scalable history.',
 'Fresh7 may use explicit reviewed checkpoint2 plus a complete raw24-hour suffix;\ncheckpoint1 remains rejected before restoring state. The exact raw trees, high/low\nphase, direct credits, immutable ordinals and royalty4 tickets are retained.\n[Setup and recovery](EARNINGS_CHECKPOINTS.md). Full raw history stays the default;\nlineage/other consumers, archival and actual workload qualification remain open.'),(
 'Checkpoint1 addresses single-deployment earnings replay, not all ownership/claim',
 'Explicit checkpoint1/2 address their respective single-deployment earnings replay, not all ownership/claim')])
edit('docs/POSITION_V7.md',[(
 'Old checkpoint1 is incompatible with profile7; use the admitted raw-history path',
 'Old checkpoint1 is incompatible with profile7; use explicit reviewed checkpoint2\n+or the admitted raw-history path'.replace('\n+','\n'))])
edit('docs/ROADMAP.md',[(
 'Fresh7 uses complete raw exact-tree replay; build and qualify explicit checkpoint2 before claiming bounded lifetime replay. Checkpoint1 remains6-only.',
 'Fresh7 supports complete raw exact-tree replay or explicit reviewed checkpoint2 for earnings. Qualify actual suffix workloads, archival/rotation/restore and operator approval before claiming bounded lifetime operation. Checkpoint1 remains6-only.')])
edit('docs/OPERATOR_MANUAL.md',[(
 '- Raw7 earnings replay is available; old checkpoint1 is explicitly incompatible.\n  Keep complete history until reviewed exact-unit checkpoint2 exists. Do not',
 '- Raw7 earnings replay and explicit reviewed checkpoint2 are available; old\n  checkpoint1 is incompatible. Keep complete raw history/WAL/backups. Do not'),(
 'Fresh7 uses full raw exact-tree replay; reviewed checkpoint2 is not implemented. Preserve raw logs/WAL and configure no checkpoint1 artifact for7. The following checkpoint1 procedure is explicitly historical accounting6/5/1 only.',
 'Fresh7 uses full raw exact-tree replay by default, or an explicitly reviewed checkpoint2. Preserve raw logs/WAL and never configure a checkpoint1 artifact for7. The same builder chooses format1 only for historical accounting6/5/1; it never converts or relabels a saved artifact.'),(
 'Use [the exact checkpoint1 procedure](EARNINGS_CHECKPOINTS.md). The offline',
 'Use [the exact checkpoint1/2 procedure](EARNINGS_CHECKPOINTS.md). The offline')])
for name in ('AGENTS.md','PROJECT_CONTEXT.md','docs/WORK_HANDOFF.md'):
 edit(name,[(
 'Fresh7 raw earnings replay works; exact-unit checkpoint2 and lifetime archival/\nworkload/recovery remain open. Old checkpoint1 is6-only.',
 'Fresh7 raw earnings replay and explicit exact-unit checkpoint2 are implemented;\nlifetime archival/workload/recovery qualification remains open. Old checkpoint1 is6-only.')])
print('Updated exact checkpoint2 source/operation boundaries; historical report bytes unchanged')
