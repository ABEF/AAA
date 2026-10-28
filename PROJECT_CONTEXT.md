# PoPL current project context

Reviewed 2026-10-28. [AGENTS.md](AGENTS.md) owns work instructions;
[README](README.md) explains the product and code; [Todo](TODO.md) alone owns task
status. This is the current snapshot, not an append-only session transcript.

## Product and implementation

PoPL is an ERC-721 collection capped at1,000 NFTs:600 Commun/300 Rare/100 Legendary.
Mint creates a dormant NFT with no LP or rewards. Activation in ETH/fixed ZZZ
attaches nonredeemable shares of shared LP; later contributions grow that NFT.
Current owner inherits unclaimed rewards, LP allocation and future funded rights.
Value/evolution is current marked on-chain LP NAV, not historic dollars contributed.

| Rule | Current candidate |
| --- | --- |
| Mint | Intended OpenSea buyer price0.05ETH gross, gas separate; recipient net after actual platform fee. Current direct mint pays all0.05ETH and is not OpenSea-compatible. |
| Contribution | ETH or one immutable ZZZ; minimum$100 activation/$5 growth, stronger pool minima apply. |
| Execution | Default2% contribution/1% conversion/3% maintenance, governance maximum10% each; caller/venue minima still apply, gas separate. |
| Prices | Two independently reviewed USD sources per priced asset,3% disagreement band; no qualified live pair yet. |
| LP revenue | Actual fees split80%NFT LP shares/10%equal activated collective/5%compound/5%ZZZ buyback-burn. |
| Royalties | ERC-2981 requests5%; actual eligible receipts shared100% at rarity weights1/2/3. Not universal marketplace enforcement. |
| Custody | No holder redemption during normal operation. Governance may irreversibly close LP and return proportional actual ETH+ZZZ directly to current NFT owners; no external custodian. |
| Maintenance | Shared ETH/ZZZ LP; one contribution pool. Accounting4 independent harvest defaults hourly; maintenance policy2 uses actual physical range exit or operator width update after the configured hard minimum (initial12hours). Operator selects ZZZ-price-in-ETH +/-25/50%; matching service adds durable1-10minute jitter/hourly ordinary inside checks. Compound capability3 has its own interval (default1hour); it yields to due rebalance and never resets that clock. Polling is not an execution promise. |

Current source profile is accounting4/governance2/fee intake1/custody3/pricing2/
Entry routing2/LP execution1/Entry review1, canonical `ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5`.
Current Position has eight fields and explicit Exited5. Production LP pools use
native ETH/fixed ZZZ only. Same-pair moves, parking and pre-exit same-chain
handoff remain. External principal/royalty custody exits, all-ZZZ exit conversion,
recovery ingress and arbitrary handoff recipients are removed. Exit includes
pending compound, preserves earned rewards and future royalties, and permanently
blocks reopening LP or canonical replacement. See
[holder exit](docs/HOLDER_COLLECTIVE_EXIT.md). Existing Anvil and accounting3
poplint remain unchanged; their evidence does not qualify accounting4.

The user is the single human operator and controls the governance wallet as well
as project services. There is no separate operator authority or committee.
Dedicated keeper/guardian/bootstrap/recipient accounts describe capabilities,
not additional people. A single-owner governance configuration is supported;
actual production wallet type/addresses remain unselected. Keep the keeper's
limited service key separate from the governance key.

Current security work includes paid-revert health visibility and post-callback keeper/pause completion checks for rebalance, compound and buyback. See [scoped review](reports/manipulation-hardening-20261027/REVIEW.md). Actual economic qualification remains open in the explicit Todo tasks for
[keeper-originated manipulation](TODO.md#task-security-keeper-manipulation) and
[outside-actor manipulation](TODO.md#task-security-external-manipulation). Qualify
actual prices, pool depth/fees and Robinhood ordering; no private submission
provider, universal anti-MEV guarantee or24-hour default is approved.

Fresh execution-quality1 separates known actual directional core fees from a1%
default additional oracle-relative loss floor (governance0-10%). Stronger gross,
caller and operation floors stay; separate reward converters keep their own
all-in policy. Strategy owns policy/revision; Manager/helper and explicit
keeper/API profiles bind it. [Feature](docs/EXECUTION_QUALITY.md), [evidence](reports/fee-impact-policy-20261028/VERIFICATION.md).
No installed service/site/Anvil changed. Passive positions and40% movement
triggers remain discussion only. The user separately requested a configurable
15-minute rebalance confirmation buffer; its observation/evidence method is
undecided and no timer is implemented. [Decision boundary](docs/LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer).

## Requested next LP policy

The [execution decision record](docs/LP_EXECUTION_POLICY.md) owns requested manual
+/-25/50% ranges, initial twelve-hour outside-only upkeep with hourly eligible
checks and durable 1-10-minute service jitter, reviewed best swap venues separate
from the LP target, useful residual reinvestment and $1m cumulative per-NFT cap.
The timing decisions are settled and implemented in fresh Strategy2/Budget3 and
matching versioned keeper/API source; no running settings/services changed.
Twelve hours is a hard initial minimum; explicit width changes can apply inside
after cooldown; compound has its own interval. LP routing1 now compares up to four reviewed native ETH/ZZZ venues with bounded
actual-core sizing and zero/one swap. Contributions swap/deploy only entrant
budgets; incumbent idle/compound remains in old NAV for guarded maintenance.
Explicit helper/runtime/parent/core/state pins and an admitted execution catalog
are required; empty catalog has no target fallback. Governed venue slippage
is1-1000bps with unchanged operating defaults/captured caller floors.
[New source review](reports/atomic-routing-20261028/REVIEW.md). [Scoped evidence](reports/maintenance-policy-20261027/VERIFICATION.md). Hourly harvest stays independent; per-currency thresholds, growing
existing LP and idle-only reinvestment already exist. No new volatility analysis,
blanket dust sweep, cumulative breaker or staged migration was selected.

Manual execution uses the existing keeper-authorized Vault.rebalance; governance
requires its own keeper grant if calling directly. It bypasses service jitter/hourly
checks only. [Operator procedure](docs/OPERATOR_MANUAL.md#manual-rebalance-at-a-chosen-time)
requires pending coordination and same-key out-of-band nonce/receipt/spend
reconciliation; LP/timer rediscovery alone does not adopt an external transaction.
The manual-execution clarification itself introduced no source/ABI/service change; later LP routing1 source and its exact evidence are separate.

## Artwork and financial reporting

Eight base colors,58 palettes, four stable pattern slots, three rarities and four
evolutions produce2,784 renderer states for the fixed1,000-entry draw inventory.
No new image generation occurs at mint. Verifiable randomness assigns a remaining
entry; provider acceptance is open. Pattern/evolution details are in
[metadata](docs/NFT_METADATA.md); current artifact bytes remain authoritative.
Enhanced starts$1,000; Singularity$10,000; market-value downgrades do not remove
activation or already earned rights. Artwork changes only after confirmed LP.

NFT fee history = individual+collective LP plus royalties, including prior claims
and past owners. Ready to claim is remaining funded balances, and lifetime claimed
is actual payouts. Claims/conversions/imports are not new income; reserves are not
NFT funds. USD history uses today's confirmed prices of original earned currencies.
Pending royalties may be claimable before processed history. Retired royalty receivers forward only already admitted
currencies; unknown new ERC20 receipts have no rescue path. Collective principal return does not
override that separate royalty admission boundary. Authentic complete
logs remain necessary despite exact index/credit/dust reconciliation.

## Source, evidence and release

Current source checkpoint is `b61aecb` on main, including fee-quality1. Earlier
LP routing checkpoint`1cabb85` retains its original scope. The
[two-day review](reports/two-day-audit-20261028/REVIEW.md) covers the ten commits
on October27-28 and fixes optional principal-delivery retry starvation. Confirmed
batch receipts clock retries (default1hour, configurable60seconds-1day); durable
priority alternates it with other jobs. Pending recovery remains first and
on-chain paid flags remain authoritative. No running service was upgraded.

Two stale Solidity comments are corrected without changing tokens, ABI, recursive
storage or compiled instructions (compiler metadata changes). New normal38size
gates and exact pins are in [verification](reports/two-day-audit-20261028/VERIFICATION.md).
Do not combine fresh backend tests with historical execution counts as one run.
Prior [atomic routing](reports/atomic-routing-20261028/VERIFICATION.md),
[upkeep policy](reports/maintenance-policy-20261027/VERIFICATION.md),
[holder-return](reports/holder-collective-exit-20261027/VERIFICATION.md) and
[earlier reports](reports/README.md) retain their original source/fixture scopes.
At that earlier checkpoint Vault24064, Manager24152 and NFT24400 left512/424/176
runtime bytes. Fresh fee-quality source has Manager24148runtime (428margin),
creation48938+160static arguments (54bytes initcode headroom);38normal gates pass.
Exact release arguments, target gas and real dependencies still need qualification.

The [Paris28October audit](reports/day-audit-20261028/REVIEW.md) reviews all five
reachable day commits and revalidates exact existing evidence without new EVM
or Python test runs. It corrects preflight/profile and keeper-reporting wording,
records the unqualified example gas budget and the pending15-minute buffer.
No new confirmed financial-accounting defect or production approval is claimed.

[Keeper safeguards](docs/KEEPER_SAFEGUARDS.md) distinguishes contract-enforced rules
from software-only jitter/simulation/budgets. Keeper personal trading around its
eligible submission time and external sandwiches remain economic qualification
questions, not proved profitable attacks or eliminated risks. Preserve the
platform-blocked simulation boundary; no attack campaign was run in this review.

Website main is `e5bb216` (read-only local check); poplint still servesf23c559 and
the unchanged demo9be6d1. Current3 unconfigured poplint is not accounting4 source
acceptance. No site/source/build/server, Anvil/NFT/LP/balance, journal, public
signing or monitor changes follow from this audit. Publication is not deployment.

**Undeployed; production NOT APPROVED.** Real feeds/routes/RPC/VRF/authorities,
OpenSea primary mint, artwork hosting, exact current-contract website/service
acceptance, strategy/gas/operating rehearsals and independent audit/remediation
remain open in the [sole Todo](TODO.md). No public deployment was requested.

## Workspace and continuation

Contract checkout: `C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2`.
Website checkout: `C:/Users/Ali/Desktop/2.x holas/Oto/aaa-website` (`ABEF/AAA-website`).
Public demonstration: [popldemo.0xwave.com](https://popldemo.0xwave.com).
Separate integration: [www.poplint.0xwave.com](https://www.poplint.0xwave.com).
The user explicitly requested keeping popldemo live and unchanged while building
poplint for current-contract integration; never exchange roots/configs/installers.
Poplint now serves websitef23c559 with HTTPS and a separate certificate-renewal
hook; operating commit77501ce adds that hook and local main e5bb216 adds resumption notes. Demo remains
on9be6d1, unchanged by before/after hashes. See the [serving receipt](reports/current3-website-20261026/DEPLOYMENT.md).
[SITE_ENVIRONMENTS](docs/SITE_ENVIRONMENTS.md) owns the hostname/build/server map.
The extra purchase-rights UI task was declined, not implemented.
Historical native2 readers retain accounting2. The new explicit current3 reader
and unsigned-review implementation belongs to poplint and has451affected JS
passes including46new methods; real contracts/API/provider qualification remains
open. Current3 fixtures use real Python DTO code with synthetic dependencies. Current selectors must be ETH/fixed
ZZZ only and reflect the captured2% default contribution budget (98% deployed),
not historical stablecoin/99% examples. Public transactions are disabled by user
decision, not a missing permission to enable them.

The [documentation reconciliation](reports/documentation-sync-20261026/README.md)
corrects superseded Todo acceptance wording without closing any of its65tasks.
Priorities are actual ETH/ZZZ prices and a cheaper ZZZ-to-ETH conversion route,
matching current3 website/read services, supported OpenSea primary-mint/VRF
integration, then exact-host operating qualification and independent review.
The source-only keeper watchdog still needs a separately authorized Linux
cgroup/signer-stop/journal/no-resend rehearsal; publication does not install it.

Preserve local Anvil/NFT/LP/balances/journals/port8902/dist overlay. Signer remains
Anvil-only, public DEPLOYMENT null, staging monitoring paused. Original dirty
documentation and older checkpoints are backed up outside Git; unrelated code
drafts remain untouched. See [resume instructions](docs/WORK_HANDOFF.md) and
[documentation map](docs/README.md). Verify Git/remote publication separately from
local saves; publication does not deploy the website or contracts.


Current selected-pool harness/RPC: [verification](reports/current-pool-fork-20261026/VERIFICATION.md)
records11successful distinct methods across scoped runs,11runner methods and a
usable keyless Pinax archive at block96,427,989. No fresh whole final11suite or
production provider/feed/VRF/authority qualification is claimed. Both inputs,
small growth and actual fee/ownership behavior pass under stated fixtures;
unfillable larger growth is rejected with atomic rollback. No guard was widened.
