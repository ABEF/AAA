from pathlib import Path
R=Path.cwd();E=Path(__file__).parent
changes={
 'README.md': [('Fresh7 has exact raw earnings replay; reviewed checkpoint2, lineage/other readers and live workload qualification remain open.',
  'Fresh7 supports raw replay or explicit reviewed checkpoint2 with raw exact-tree state and a complete rolling-day suffix; lineage/other readers and live workload qualification remain open.')],
 'docs/FRONTEND_API.md': [('Accounting7 rejects checkpoint1 before restoring state and uses complete bounded\nraw history. Exact-LP checkpoint2 remains open. Other history/preparation\nconsumers are not silently switched to checkpoints.',
  'Accounting7 rejects checkpoint1 before restoring state. It supports complete\nbounded raw history or explicit reviewed checkpoint2 for earnings, retaining\nraw trees/phase/direct credits and the complete rolling-day suffix. Other\nhistory/preparation consumers are not silently switched to checkpoints.')],
 'docs/ACTIVATION_PREPARATION.md': [('Raw earnings replay is supported; historical6 checkpoint1 is not a7 seed and\nexact checkpoint2 remains open. [Policy semantics](ADAPTABLE_POLICY.md).',
  'Raw earnings replay and explicit reviewed checkpoint2 are supported; historical6\ncheckpoint1 is not a7 seed. This does not change contribution/preparation reads\nto checkpoints. [Checkpoint scope](EARNINGS_CHECKPOINTS.md), [policy semantics](ADAPTABLE_POLICY.md).')],
 'docs/DEPLOYMENT_WEBSITE.md': [('Fresh7 raw earnings use exact LP events/getters; checkpoint1 is historical6-only\nand exact checkpoint2 remains open. These are backend source boundaries, not a',
  'Fresh7 earnings use exact LP events/getters and optionally reviewed checkpoint2;\ncheckpoint1 stays historical6-only. These are backend source boundaries, not a')],
 'docs/ROYALTY_REPORTING.md': [('currency cursors, opening/cutoff state and whole royalty units. Fresh7 rejects\ncheckpoint1 and uses complete raw replay; exact checkpoint2 remains open.',
  'currency cursors, opening/cutoff state and whole royalty units. Fresh7 rejects\ncheckpoint1 and uses complete raw replay or explicit reviewed checkpoint2, which\npreserves those royalty4 rights alongside exact LP trees/phase/direct credits.')],
}
for name,pairs in changes.items():
 p=R/name;raw=p.read_bytes();s=raw.decode().replace('\r\n','\n');orig=E/'original-docs'/name
 orig.parent.mkdir(parents=True,exist_ok=True)
 if not orig.exists():orig.write_bytes(raw)
 for old,new in pairs:
  assert s.count(old)==1,(name,old[:70],s.count(old));s=s.replace(old,new)
 p.write_bytes(s.replace('\n','\r\n').encode()if b'\r\n'in raw else s.encode())
print('Reconciled current API/activation/royalty/website source guides; historical reports untouched')
