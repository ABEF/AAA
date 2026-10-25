# Source-scoped verification - 2026-10-25

Baseline main `80d330ea51abacdfb825af24730badb26e6bd83d`.
Read [findings](REVIEW.md), [coverage/decision review](COVERAGE.md),
[core review](CORE_REVIEW.md) and the separate publication receipt.
**Production NOT APPROVED.** This is not a full fresh regression or an
independent audit. Final source/content identities are recorded separately.

| Scope | Actual evidence | Qualification boundary |
| --- | --- | --- |
| Reviewed Entry/Pricing/Registry | [26 distinct underlying Solidity methods pass](entry/VERIFICATION.md), across27suite/test IDs and28invocations including one repaired rerun and one inherited duplicate. Exact input scopes/diagnostics retained. | Real Entry/Pricing and installed-v4 local paths with explicit local dependencies; not actual Robinhood/provider/wallet qualification. Legacy raw Vault calls retain their own interface. |
| Exact preparation/trace/profile/inventory | [98/98 frozen affected Python cases pass](entry/python-final-bound.json), with [full log](entry/python-final-bound.log) and final per-file bindings. | Mocked RPC/trace/ABI/configuration composition. Initial97 had95passes/two fixture errors, retained as diagnostic observations; later incremental checks are not added to98 again. |
| Metadata and buyback | [51 distinct scoped Solidity passes](core/VERIFICATION.md):10metadata and41buyback; two existing fuzz properties each1,000runs. | Real renderer/Oracle/protocol accounting with declared feeds/authority/assets/venue substitutes. Eight unchanged metadata test bodies/shared harness are reused explicitly; only two repaired new fixtures rerun. |
| Indexer/database/history | [28 distinct affected methods pass](backend/indexer/receipt.json), including actual SQLite-to-API history integration and bounded-depth/genesis cases. | Offline chain/RPC fixtures and temporary databases. The original missing/malformed-header behavior reproduces12failed subcases before the fix; no actual service database changed. |
| RPC transport and budgets | [22 distinct methods pass](backend/rpc/receipt.json), including real isolated loopback trap endpoints. Original301/302/303 requests reached the trap; final tested3xxstatuses make zero trap requests. One later429/500resource-close method adds only one distinct case. | Configured chain-checked failover and work limits retained. Closing handles/refusing redirects tested locally; no actual provider, proxy or hosting acceptance claimed. |
| Normal deployment sizes | [37 object gates pass across42 final production sources](core/production-final-size-gates.json). Root independently checks all42source hashes against the receipt. | Solidity0.8.26/Cancun, existing via-IR/optimizer profile; runtime/initcode limits unchanged. Dynamic constructor arguments require exact release encoding; supplied URI/role-array examples are illustrations. |
| CI selection/docs/provenance | Final validation checks generated Todo, changed-document relative links, workflow suite selection, exact source/evidence hashes, scoped diff and preserved unrelated files. | Local inspection is not a completed remote CI workflow or Linux operating rehearsal. Publication must be independently read from Git/receipt. |

## Failure diagnostics and deliberate reuse

The [core receipt](core/receipt.json) retains the metadata red control, a rejected
Foundry `testFail*` harness name, the repaired red control and the exact secondary-
source error assertion repair. Two metadata owner-prank fixtures initially
consumed their one-shot prank with a getter; only those cases were rerun after
caching the immutable receiver. These are documented test corrections, not
hidden production passes.

The [backend receipt](backend/REVIEW.json) and per-component logs retain original
outage/redirect/resource failures. RPC handle-close refinements repeat only
affected cases and do not inflate the distinct count. Entry's final98backend
selection was rerun once after actual compatibility/DTO/service-profile changes,
with saved final bindings rather than invented historical hashes.

The single SQLite-to-history integration was selected from a file containing
two unrelated local draft tests. [AST reuse proof](HISTORY_REUSE.json) establishes
that the executed method and complete supporting module/class/harness code
match published HEAD; only those two unexecuted methods differ. They remain
outside publication, and the integration was not repeated just for a new count.

Historical full inventory/randomness, royalty accounting, custody/canonical
handoff, strategy/keeper and maximum-state cold-gas reports retain their original
source scope. Unchanged suites were not rerun merely for counts. Old
`ActivationEntry.t.sol` mocks without the Pricing helper are not current native
integration evidence; this pass does not claim they constitute a green full CI.
Do not substitute an old passing report or exact-commit remote workflow for a
new frozen-release qualification.

## Final normal size observations

| Object | Runtime | Creation including fixed arguments |
| --- | ---: | ---: |
| Vault |24,519bytes (57margin)|47,372bytes|
| Registry |12,027bytes|48,334bytes (818margin)|
| Reviewed Entry |17,511bytes|30,116bytes|
| ContributionPricing |15,200bytes|15,918bytes|
| Buyback |7,838bytes|8,628bytes|
| Metadata renderer |12,831bytes|13,187bytes|

NFT creation44,097bytes and AccessController creation40,832bytes exclude dynamic
arguments. Exact release URI and proposer/executor arrays must be encoded and
checked; illustrative totals44,289and41,120are not approvals of actual choices.
See the full gate receipt. The final Vault still has little runtime headroom;
neither gate nor compiler configuration was increased to fit changes.

## What was preserved and not qualified

No website source/build/server,8902/Anvil/NFT/LP/balance/journal/dist-overlay,
actual deployment configuration, signer permission or monitoring service was changed.
The blocked production example now declares required reviewed-policy capabilities;
it contains no newly qualified deployment/provider observations or release approval.
Website repository changes are memory only. Public DEPLOYMENT stays null,
signing remains Anvil-only and monitoring paused. No public transaction,
deployment, sealing, key use or live service action occurred.

Actual independent feeds/routes/VRF, native browser/wallet/OpenSea integration,
authorities/artwork hosting, market/strategy economics, full target-chain gas,
Linux/provider recovery and independent audit/remediation/sign-off remain open.
Per-operation policy binding is not protection against trusted governance
admitting malicious dependencies or an external custodian withholding assets.
