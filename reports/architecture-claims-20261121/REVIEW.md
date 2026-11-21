# Audit of the seven technical presentation claims

21 November 2026. Contract source baseline:
`6d324a28459eca77d15a73fe227b4457728d6889`.
Website source inspected: `69c4b621d91fd16d16cc15671cca7dd51c7b79ac`.

**All seven areas have implemented components. This does not establish complete
integration, universal safety or production readiness.** No new production-code
defect was confirmed in the inspected paths. Three documentation categories were
corrected; existing qualification and consumer gaps remain open.

## Scope and method

Trace the seven presentation statements through current contracts, keeper,
indexer, API and website source; compare saved evidence with its actual source,
fixtures and adoption boundaries. Three independent read-only reviews cover LP/
security, economic rights/exit and consumer/readiness. Keeper scheduling and
recovery are additionally inspected directly. This is a source/evidence audit,
not a fresh exhaustive execution of all ABI functions or a live-site inspection.

## Findings corrected

| ID | Severity | Confirmed issue | Correction |
| --- | --- | --- | --- |
| AC-01 | Documentation | Two exact-accounting guides still state a mandatory 20M contribution ceiling; royalty settlement also fails to distinguish that historical measurement from the selected candidate. | State the non-live 32M/full20% candidate, maximum estimate 26,666,666, unchanged legacy12M default and separate explicit adoption. No configured limit is changed. |
| AC-02 | Documentation | Initial royalty receipts are described as allocating automatically when the opening deadline passes. | The deadline fixes the eligible cohort; the next successful synchronization or holder claim materializes allocation. Time alone submits no transaction. |
| AC-03 | Documentation | Optional currency failure is described as never undoing activation. | Continuation applies to supported faults in sufficiently funded isolated frames. Insufficient partial frames and other invalid conditions revert to preserve entitlements; healthy-only claims remain separately selectable. |

Corrections are in [exact royalties](../../docs/EXACT_ROYALTY_ALLOCATION.md),
[exact LP accounting](../../docs/EXACT_LP_ALLOCATION.md) and
[royalty settlement](../../docs/ROYALTY_SETTLEMENT.md).
AC-03 matches `ZZZRoyaltyRewards._syncActivationAsset` and `_activationBalance`:
the authenticated full-frame/read-failure distinction cannot be removed merely
to allow caller-induced gas starvation.

## Seven-area source audit

| Area | Source support | Necessary qualification |
| --- | --- | --- |
| ERC-721, activation and growth | [NFT](../../src/ZZZNFT.sol), [Entry](../../src/ZZZActivationEntry.sol), [Vault](../../src/ZZZVault.sol) attach shares to NFT IDs; current-owner claims follow ownership. Entry checks the exact ETH/fixed-ZZZ input and operation policy. | Financial rights do not include ordinary holder principal redemption. NFT ownership can be an escrow or contract address. The production OpenSea mint path remains unqualified. |
| Managed Uniswap v4 liquidity | [Position executor](../../src/ZZZLPPositionExecutor.sol) bounds the physical portfolio to a main and optional residual in the same pool, with Vault custody, actual amounts and both-leg collection/closure. | The residual is one-sided when created; it can become mixed or filled. The main/residual allocation floor applies at replacement, not continuously. Neither position guarantees constant USD value. |
| Rewards, royalties and terminal return | [Fee controller](../../src/ZZZFeeController.sol), [LP rewards](../../src/ZZZRewards.sol), [royalty rewards](../../src/ZZZRoyaltyRewards.sol), [migration/return](../../src/ZZZMigration.sol) implement separate funded rights, reserve classification and current-owner payouts. | See the economic and exit boundaries below. Exact whole-unit assignment is not a promise of immediate payout of every received currency or exact fractional fairness for tiny receipts. |
| Permissions and execution checks | [Module authority](../../src/base/ZZZModule.sol), [Oracle](../../src/ZZZOracle.sol), [contribution pricing](../../src/ZZZContributionPricing.sol) and [budget](../../src/ZZZMigrationBudget.sol) check roles, reviewed sources, callback state, deployed marginal LP and bounded execution. | Source identities do not prove economic independence. Actual independent sources/routes remain unqualified. Paused governance emergency operations can explicitly omit selected financial guards. Reversion rolls back that transaction's state, not gas or an earlier confirmed approval. |
| Keeper automation and recovery | [Keeper](../../keeper/monitor.py) recovers pending first, checks current authority/lifecycle, schedules maintenance and independent hourly harvest, and supports configured compounding/buyback/LP-conversion jobs. Durable intent precedes Cast; [bounded capture](../bounded-cast-20261121/REVIEW.md) preserves uncertain-send recovery. | Jobs require reviewed configuration, funding and dependency availability. Extra in-range compound waiting is service-only by operator decision. Full normal-daemon/real-Cast Ubuntu, off-host restore and sustained operation remain open. No original-currency royalty conversion worker is required or enabled. |
| Data, history, API and website | [Indexer](../../indexer/monitor.py), [history](../../frontend_api/history.py), [read service](../../frontend_api/service.py) and [unsigned preparation](../../frontend_api/transactions.py) exist with bounded work and explicit profiles. | The website still uses the legacy complete ownership endpoint; backend fixed-block16-ID pages are not adopted there. Local source10 differs from served historical current3. Popldemo is simulation; poplint is separate read/unsigned integration. Public signing remains disabled. No live endpoint or website was rechecked. |
| Verification and readiness | Current source-bound construction, contribution, fee/claim, maximum-state and recovery evidence is recorded in [the roadmap](../../docs/ROADMAP.md), [workload map](../../docs/WORKLOAD_COVERAGE.md) and immutable reports. | Finite fixtures and reused evidence do not cover every market/state. No complete acceptance package or production gate is approved. The maximum-state direct activation shortfall, actual providers/fees, markets, authorities, OpenSea/VRF/content, adopted consumers/operations and independent review remain open. |

### Economic and exit boundaries

- LP fees are split when actually harvested. In each asset, multiples of20 raw
  units fund16 individual /2 collective /1 compound /1 buyback. A tail below20
  is carried; settlement barriers assign that tail to incumbent individual
  rewards. Compound/buyback reserves are not claimable holder income. Harvest
  itself does not perform compounding, conversion or burning.
- LP ETH and fixed-ZZZ source claims exist. The normal consumer's intended
  ETH-only settlement requires a separate qualified conversion path; direct
  source-asset evidence does not qualify that path. Conversion is not new income.
- Royalties pay admitted currencies as received, using activated rarity1/2/3
  weights, exact-unit remainder rules, the one-hour opening and fault cohorts.
  Prefunds, unsupported receipts and zero participants have explicit allocation
  requirements. A broken token or incompatible receiver cannot be guaranteed
  to pay. [ERC-2981](https://eips.ethereum.org/EIPS/eip-2981) signals a royalty
  amount/recipient; it does not universally force a marketplace payment.
- Terminal holder return is paused-governance-authorized and irreversible.
  All buckets close and allocation reaches Ready before payouts begin. A broken
  bucket can block that transition. Bounded governance distributions isolate
  failed owners; each NFT's ETH+ZZZ payout is atomic and failed amounts remain
  backed for retry or the existing current-owner fallback. NFTs retain transfers,
  previously earned rewards and future royalty rights. There is no new custody
  address or integrated bridge.

The underlying ERC-721 ownership model is described by
[ERC-721](https://eips.ethereum.org/EIPS/eip-721). The same-pool physical-position
and settlement review uses the actual pinned dependencies; Uniswap's
[PoolManager documentation](https://developers.uniswap.org/docs/protocols/v4/concepts/poolmanager)
describes the singleton and final settlement checks, not PoPL-specific release
approval.

## Verification and preserved state

- Documentation-only changes: no Solidity, production Python, website, ABI,
  profile, safeguard, permission, accounting or economic-rule changes.
- Original edited guides/ledger/index bytes were archived and hashed outside
  Git before changes. Four unrelated tracked dirty files remain byte-identical
  and are excluded from publication.
- Todo generation/consistency, targeted links, exact task IDs/statuses and Git
  diff boundaries are checked. No old test, suite, compiler, fork, gas campaign,
  public transaction, live-site probe or operating rehearsal is rerun.
- The Operator manual already describes the selected gas candidate and funded
  failure rules; the launch-window guide explains transaction-driven opening.
  No function/input/permission or procedure changes are needed; the corrected
  specialist guides are brought into agreement with those procedures.
- Existing Anvil, NFTs/LP/balances, sites, services, journals/checkpoints,
  credentials and user-paused heartbeat remain untouched. Source publication
  grants no deployment, sealing, signing or service rollout approval.

The Todo records this reconciliation without closing market, consumer or
operating acceptance tasks. Existing historical report bytes and their test
counts/source scopes are unchanged.
