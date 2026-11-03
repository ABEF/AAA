# Source-bound authority verification

Fresh custody5 normal compiler output02caecbef6, based on main db8033ec. This is
selected internal verification, not a fresh full suite, published CI, actual
operating acceptance, independent audit or approval to deploy.

## Actual source and build

[Normal gates](production-size-gates.json) bind52 production sources/31 exact
dependencies and all43 runtime/initcode gates under Solidity0.8.26, Cancun,
viaIR/optimizer1/Yulfalse. Only production ZZZMigration changed. Final runtime24537
(39bytes margin), creation34385 before32byte arguments. The failed first compile
is retained: runtime24596/margin-20. Build driver exit0 alone was not a gate pass.
No limits were relaxed for normal objects. Public ABI/storage and account6 wire
remain; custody getter deliberately changes4→5.

## Targeted EVM execution

14 distinct selected methods pass across explicit source/test scopes: the first
stage passed13/14 and failed one newly written test. Its expectRevert was consumed
by the royalty-ledger getter before the intended claim call; moving that getter
before expectRevert corrected the test. Only that failed test was rerun, and it
passed. Production source was unchanged between stages. Do not sum attempts as15
behaviors. Tests cover unauthorized owner/keeper batches, successful governance
batches, inability of governance to claim another owner's LP/royalty/principal,
proportional conservation, claims/transfers/future royalties after exit, receiver
rejection/reentry, prefund separation and actual Access role/sealing/handover cases.

The holder fixture uses MockAccess with real Vault/NFT/reward/Migration logic and
deterministic venues/feeds/VRF. Selected AccessController tests exercise the real
controller separately. EVM fixtures use the existing test-only large-size allowance;
normal production limits are checked separately above. No live chain was reset.

## Backend and profile evidence

25 corrected targeted Python methods pass, no failures/errors/skips, covering
explicit custody5/old-runtime rejection, price-outage funded reward reads,
per-peer lineage versions, disabled keeper batches/pending-first recovery,
schema10 observation/old-profile rejection and strict source-bound offline review.
Earlier stage63 executions had0 assertion failures/4 errors: three new observer
cases exposed an incorrect ZERO_HASH namespace and one operator setup correctly
rejected the then-stale callable source binding. Both were corrected before this
scoped rerun. Imported fixture test discovery duplicated methods in the first
stage; no counts are added across stages. Other first-stage successes are retained
as scoped evidence, not called a full current suite. [Campaign ledger](campaigns.json).

No real RPC/provider, external wallet, public signing, real recipient payment,
actual gas/uptime or frontend rollout was tested here. Profiles remain source-only.
Current function reference37/818/37/13 has0 gaps and explicit permissions.

## Static review

Fresh actual Slither0.11.6/crytic0.4.2 used exact closed compiler source maps/AST,
without recompilation.471 emitted records:19 current contexts reviewed,452 exact
unchanged referenced-source/context dispositions reused. High73/Medium92/Low209/
Informational76/Optimization21 are raw detector categories, not confirmed exploit
counts. All emitted records have internal dispositions; this is not a clean scan.
Analyzer process returned4294967295 for findings while JSON reports success=true,
error=null. Source unchanged and full raw output remains in external evidence.
[Review](static-review.json), [coverage](static-coverage.json), [execution](static-execution.json).

Current AST construct inspection, publication closure, CLI profile checks and
maintained document links are recorded separately in the final consistency record.
Old compiler advisory snapshots remain historical; fresh official advisory
qualification is still a frozen-release requirement, not inferred from old runs.

## Evidence and preservation

External raw root:
C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/authority-audit-20261103.
BASELINE pins111 original current files,485 code/config/test/build records and2634
historical report artifacts, including the report index. Original dirty files and
failed sources/builds/test stages remain archived. Historical reports are unchanged
except maintained reports/README navigation. Four unrelated tracked dirty files
remain byte-identical and excluded from this publication. Existing deployments,
sites/services/Anvil/NFTs/LP/balances/journals/signing/heartbeat remain untouched.
