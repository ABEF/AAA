# Verification and source boundaries

Baseline53633b9,13November2026. Production changes are read-only probe resource
handling and indexer failure scheduling. Runner registration is one module-list
addition. No Solidity, ABI, economic control, signer or live state change.

| Area | New verification | Important limits |
| --- | --- | --- |
| Probe |13unique new methods pass at final source42142395…; real Rpc chain/parser over inert transport and fake clocks | Earlier11/final13stages overlap. Baseline initial stdout is retained only as a labelled summary, not fabricated raw logs. One draft pacing assertion was corrected; exact corrected scenario fails against immutable baseline. Final clock-capture regression fails before its fix. No public network run. |
| Indexer | All7unique new methods pass together on finalef7796e5… source | Initial28failed subtests across four negative methods; positive size/payload/one-block cases passed. Reserved-code cases fail18baseline subtests. Final review adds10locally generated terminal diagnostic cases, which fail on the prior candidate. The final full7run is justified by the changed helper; earlier7/one/two stages overlap and are not extra unique methods. |
| Failed harness | An initial byte replacement wrongly assumed CRLF on LF source and changed nothing | Its repeated new-only failures are preserved as unsuccessful evidence, not a corrected result. No old suite was run. |
| Inventory | New13probe methods registered in keeper runner; general discovery includes the7indexer methods | Inventory mode executes0tests. Source brackets must be stable; selected counts are not pass counts. |
| Task review | All44unique owners have concrete source/obligation views and original310record links | Contract34/backend16/keeper9views overlap. Source inspection is not fresh execution, full independent audit or release acceptance. |
| Peer review | Current probe/indexer/test/shared-RPC/error/work-budget pins reviewed read-only | No blocking correction found; no tests rerun. Reorg rollback may precede a later failed fetch. |

Unchanged61production Solidity and100compiler-input sources retain exact
accepted bytes. The previous normal48gates and strict567static record are
source-bound reuse, not rerun. Existing controlled gas/market/browser/EVM suites
are not repeated. General Rpc, keeper monitor/health identities, financial
limits, default12M and opt-in20M/24M policies stay unchanged.

The changed probe/indexer files are absent from checkpoint1/2source lists; this
edit alone requires no checkpoint rebuild. Preserve raw/WAL backups, actual
source/runtime/configuration pins and original pending journals. Optional CLI
pacing has local synthetic evidence only; the earlier public13-check profile
keeps its exact older source and wrapper provenance.

The initial whitespace check flags10trailing-space lines in retained raw
unittest failure logs. Their exact captured bytes are preserved. The check passes
for source, documentation and non-log evidence with only those raw log files
excluded; no source formatting failure is ignored or original log rewritten.

See each partition's retained logs/source hashes and [completion](COMPLETION.json)
for mechanical integrity, introduced links, sole-Todo generation, references,
protected-file preservation and exact staged/committed publication checks.
No provider/cadence/market/host or production approval is inferred.
