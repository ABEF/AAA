# Architecture review and adversarial assessment

Review started 2026-10-16, continued 2026-10-17 on
`codex/architecture-evolution-review`, baseline `37bf0d220344736e3fcab35c64ff3386a3d57bfa`.
This is an internal assessment of an undeployed candidate, not an independent
audit or production approval. See the [corrected prompt](REVISED_PROMPT.md) and
[architecture design](../../docs/ARCHITECTURE_EVOLUTION.md).

## Assessment and scope

The shared-pool model does not need 1,000 individual LP maintenance transactions.
Stable NFT shares and token-specific reward indexes are the right foundation.
The critical limitation is extensibility across **different asset compositions**
and **canonical ownership chains**, not the number of NFTs. Current v3 migration
preserves an original home pair/identity; it cannot safely be advertised as an
arbitrary pool, DEX or canonical-chain migration system.

Keep the fixed 80/10/5/5 split and separate 1/2/3 royalty weights. Their immutability
reduces governance risk for holders who cannot redeem principal. The proposed
3% aggregate migration execution budget is a new design requirement; it is not
present enforcement and does not authorize changing the 1% activation budget.

The review read custody, migration, transport, registry, fee/reward, membership,
NFT, access, entry, pricing, manager and operational boundaries, plus the separate
website sources and prior receipts. New execution evidence is deliberately
limited to changed or uncovered paths; historical results are not relabelled.

## Findings and architectural risks

Severity indicates potential impact under the listed preconditions. A privileged
trust risk is distinguished from an unprivileged exploit. No claim is made that
every possible defect has been found.

| ID | Severity / category | Preconditions and impact | Resolution / evidence boundary |
| --- | --- | --- | --- |
| AE-01 | High availability in the baseline; locally repaired | Governance reserves a pool, then other approved first arrivals fill all four historical slots before delivery. The old implementation rejects the reserved arrival; externally delivered funds may require provider recovery. No incumbent local theft demonstrated. | Permanent idempotent capacity admission is implemented with source-bound regressions. Source still does not verify remote admission proof; external qualification remains a migration release gate. |
| AE-02 | Critical custody trust if maliciously admitted | A correctly pinned approved provider consumes exact principal but does not fund destination. Exact balance depletion and a receipt cannot prove remote custody/backing. | Demonstrative real-router test; keep real bridges disabled. Independently qualify each provider/destination and its administration. No generic local fix proves arbitrary future code honest. |
| AE-03 | High architectural incompatibility | Governance wants ZZZ/WETH -> ZZZ/USDC. Pair guard rejects it; removing that guard would leave immutable old inboxes, home-currency reward paths and v3 liabilities inconsistent. | Preserve rejection; document composition epochs and typed conversion. Implementation requires bounded historical intake/asset obligations and a new authenticated protocol version. |
| AE-04 | Critical catastrophic continuity risk | Canonical home chain permanently stops or cannot process ownership/claims, even while remote LP continues. LP migration leaves canonical NFT and two reward ledgers at home. | User selected planned whole-protocol freeze/export/import while the source works; implementation and finality qualification are pre-seal requirements. Post-halt recovery is deferred; no universal snapshot recovery claim. |
| AE-05 | High economic trust | Governance admits false price feeds, a compromised token/wrapper or harmful routes; keeper repeats permitted lossy operations. Local permission/slippage tests can pass while holders lose value. | Retain bounded parameters and source pins, require feed/admin/venue review and strategy/MEV rehearsals. Record cumulative migration costs. A per-move 3% cap is not profitability or independent oracle truth. |
| AE-06 | High availability | Fixed coordinator fails to fulfill an early ordered VRF request. Later reveals and activation can remain blocked. | Existing tests/source establish ordered dependency; no redundant rerun. Live provider qualification and a fairness-preserving continuity decision remain open; no administrator reroll added. |
| AE-07 | High integration gate, not current simulated-wallet exploit | Live UI adopts Number-based example IDs or trusts unsigned API targets without independent chain/account/identity checks. Hashed uint256 IDs may be rounded; stale or substituted transactions could be signed. | Keep simulation separate. Require exact decimal strings, independent deployment/asset validation, draft expiry, wallet checks and canonical receipt handling. Backend preparation is still unpublished. |
| AE-08 | Medium operating/availability gate | Missing off-host state, competing signer hosts, nonredundant RPC/fee service, missed alerts, provider or token outage. Staging snapshots alone do not prove unattended recovery. | Reuse exact-source keeper evidence; do not equate Anvil/desktop heartbeat with target-chain production or continuous uptime. Distinct-host loss/rotation and real services remain release gates. |

Primary source paths: [Vault](../../src/ZZZVault.sol),
[BridgeRouter](../../src/ZZZBridgeRouter.sol),
[Migration](../../src/ZZZMigration.sol),
[FeeController](../../src/ZZZFeeController.sol),
[NFT](../../src/ZZZNFT.sol), [Oracle](../../src/ZZZOracle.sol),
[access controller](../../src/ZZZAccessController.sol).

## Failure modes and recoverability

| Failure | Funds / rights at risk | Existing response | Residual limit |
| --- | --- | --- | --- |
| Keeper offline for days | Range quality, harvest/compound timing and metadata freshness | Persistent nonce/receipt/budget recovery and chain-state discovery | No guaranteed yield; qualify real restart, fees and independent alerts. |
| Broken source price or creator inbox | Normal upkeep/departure availability | Timelocked paused close-only parking with exact raw minima; designated custody retained | Failed token, venue or wrapper can still prevent close. Resume needs fresh prices. |
| Source route disabled after departure | Old receipt settlement | Historical policy/routes remain for authenticated inbound | Changed provider code/config or lost backing can still block settlement. |
| Delayed/duplicate/reordered packet | Principal/reward counters and current custody epoch | Nonces, identity, funding, epoch and old-liability checks | Real SDK semantics/backing need independent proof and rehearsal. |
| Destination fills before arrival | Delivery availability | Permanent reservation repair | No automatic source-side remote capacity proof; governance can waste all four slots. |
| Late old-currency fees after pair change | Holder liabilities and compound reserves | Current code rejects different-pair transition | New epoch/intake policy required; never silently drop or relabel funds. |
| Reward token blacklists or changes transfer behavior | Claims and membership settlement | Admission review and exact transfer rejection | Quarantine/fail-closed protects accounting, but does not restore token liveness. |
| Governance signers lost | New configuration, unpause, migration | Multisig operational recovery outside contracts | No hidden recovery key; a timelock is not key recovery. |
| Home chain halts and later restarts | Duplicate canonical rights after an improvised replacement | No current replacement mechanism | Any future recovery must address competing histories and revoke/freeze old rights. |

## Evidence discipline and second review

Before edits, actual hash comparison found all 29 production sources, the 73-file
offline Solidity closure and 76-file prior fork closure unchanged. The older
static source/config closure also matched. The broad Python receipt did not
fully match because the Todo generator changed; older frontend receipts also
include superseded keeper/RPC code. Only matching scoped evidence is reused.

Changing Vault invalidates prior whole-Vault runtime, static and fork coverage
as current-source evidence. New targeted reservations, returns, switching,
gas/size and trust tests must be reported separately; the historic 531-pass
suite is not a fresh whole-candidate result. No public chain transaction or
production contract deployment is part of this review.

The architectural brief was challenged by separate custody and authority reviews
before source edits. They agreed on the capacity repair and rejected a shortcut
that merely removes currency checks. The frontend/operations review separately
checked `None` bucket enumeration and evidence reuse. See the verification
record for execution results and the final source review.

## Release decision

**NOT APPROVED.** Local admission repairs do not close asset-composition,
canonical continuity, real bridge, market/service, authority, independent audit
or live frontend gates. All task progress and acceptance criteria remain in the
[central Todo](../../TODO.md), not duplicated here.
