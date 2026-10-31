# Work handoff

Reviewed31October2026, Europe/Paris. Read [instructions](../AGENTS.md),
[context](../PROJECT_CONTEXT.md), [README](../README.md), [sole Todo](../TODO.md)
and the relevant [operator procedure](OPERATOR_MANUAL.md).

## Current source and preserved environments

Fresh [accounting6](POSITION_V6.md), ProtocolPolicy1, Portfolio2, Entry2,
maintenance3/confirmation3/compound4, custody4/emergency2/LP-routing2, schema8
inventory and canonicalV6 are the current undeployed source candidate.
[Policy controls](ADAPTABLE_POLICY.md) and [exact operator inputs](OPERATOR_MANUAL.md#future-operating-settings)
explain future mint/entry terms, scoped idle/gas/display settings, drained VRF
rotation, per-pool main allocation/gap and reviewed buyback maximum.

Defaults remain0.05ETH direct mint,100USD activation/5USD growth,60%minimum main,
half-side residual with one-spacing gap and existing loss/gas settings. Main floor
may rise6000–9999bps; lowering below60% was not authorized. Fixed ETH/ZZZ,80/10/5/5,
rarity weights, original ownership/rewards/backing and terminal holder return remain.
Fresh reviews bind exact scoped policy; callback changes cannot weaken them.

No deployment, sealing, service/site/Anvil/journal/signing or heartbeat change.
Existing Anvil8902 and its NFTs/LP/balances/transaction recovery remain untouched.
Popldemo keeps its simulation; poplint keeps the separately served current3
read/unsigned build. Source6 is not an upgrade to either. Public DEPLOYMENT stays
null and browser signing Anvil-only. The user-paused heartbeat stays paused.

## Evidence to reuse, with limits

[Current verification](../reports/adaptable-policy-20261031/VERIFICATION.md) binds
52 production sources and31 dependencies to normal-final-0a0cac9f06:43 normal
EIP170/EIP3860 gates, unchanged0.8.26/Cancun/viaIR/optimizer1/Yulfalse.
Vault23941runtime(635margin), Budget24339(237), Migration24556(20), NFT22192(2384).
Changes require new exact-source gates; these are not target-chain gas estimates.

The reference has37concrete contracts/826function rows/37constructors/14receivers,
zero explanation/input/output gaps. Scope-limited EVM/backend executions, fixture
failures, corrected retries, empty attempts and reused bodies are recorded in the
report, not combined into a fictional full current suite. Earlier42-gate/778-callable/
463-static reports remain historical and do not verify later policy changes.
No full-suite/CI/live qualification or independent production approval is implied.

Raw source/evidence/archive root:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/adaptable-policy-20261031`.
It preserves365 original files and49 prior report artifacts. The later final
sync archive is `documentation-sync-20261031-47ead73e` under the same external
visualization root; it preserves105 current documents and1795 report hashes.
Documentation sync reuses unchanged code evidence and does not rerun contracts.

## Continue next

The [current follow-up](../reports/today-audit-20261031/REVIEW.md) fixes exact
publication closure and predecessor dependency admission; its
[verification](../reports/today-audit-20261031/VERIFICATION.md) distinguishes useful
affected accounting/API checks, current static contexts and final0a build reuse.
Check committed/staged Python imports, not only local files. No old journal or
service is adopted by these source repairs.

1. Establish publication state from exact local/remote main heads. Git publication
   is not deployment or qualification. Keep source, docs and linked evidence
   together; preserve the unrelated dirty files and drafts below.
2. Qualify actual independent dual feeds, reviewed swap/conversion routes, RPC,
   VRF provider/subscription/funding and governance/guardian/keeper/payee addresses.
   Pending draws must drain before planned VRF rotation; no reroll fallback.
3. Build reviewed source6 service configurations and a fresh indexer contract
   inventory/database including ProtocolPolicy. Enabled conversion jobs require
   an explicit profile. Preserve pending recovery first and old journals; a
   JSON edit or runtime label cannot upgrade installed code or adopt old state.
4. Complete source6 poplint read/unsigned consumer integration, keeping popldemo
   and public signing unchanged. OpenSea primary-mint integration remains open;
   direct mint does not implement marketplace buyer/payment semantics.
5. Qualify target gas/constructor arguments, liquidity/strategy economics,
  600/240/300 sampled timing, jitter, Linux storage/restart/recovery and exact
   authorities. Migration's20-byte runtime margin needs care in any future edit.
6. Refresh source-bound static analysis and independent audit/remediation for
   this candidate; complete metadata hosting, operating rehearsals and release
   sign-off. Production remains NOT APPROVED.

## Preservation and ongoing documentation

Four unrelated tracked dirty files stay byte-identical:
reports/source-checks.json, scripts/run-fork-checks.py,
tests_python/test_fork_runner.py, tests_python/test_frontend_history.py.
Original hashes are in the external baseline. Do not stage them, design drafts,
cache/out directories or unrelated old operational artifacts.

Historical [portfolio](../reports/optional-portfolio-20261030/VERIFICATION.md),
[residual operation](../reports/residual-operations-20261031/VERIFICATION.md),
[day audit](../reports/day-audit-20261031/VERIFICATION.md) and
[manual-operation](../reports/manual-operations-20261031/VERIFICATION.md) records
retain original bytes/source scopes; use the report index instead of copying
old checkpoints into current memory. Older documentation originals also remain
at the archive recorded by [cleanup publication](../reports/documentation-cleanup-20261026/PUBLICATION.md).

Maintain one ledger → generated Todo. Keep features, roadmap, release scope,
operator procedures, callable reference and repo context consistent. Check links,
generated artifacts and exact unchanged code pins for docs-only changes; do not
claim new implementation/release completion merely from documentation.
