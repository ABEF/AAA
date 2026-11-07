# Canonical handoff: same-chain implementation

## Current exact-LP and exact-royalty compatibility

Fresh canonicalV9 uses ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_V9; V8 and older
peers are rejected. The royalty header remains five words (currency count, NFT
count, total weight, closed mint end, capacity). Royalty asset rows are192bytes
(asset, raw allocation cursor, accounted, liabilities, unallocated, backing).
NFT weight rows are128bytes (id, weight, activation ordinal, ticket start).
NFT/currency rows are96bytes (id, asset, accrued whole units).

Frozen view export flattens accrued plus all outstanding normalization-book
units. Source books stay intact for abort; the importer starts empty books and
flat accrued units. Import proves unique complete ticket/ordinal coverage,
rarity, cursor/GCD bounds and each currency's summed claims equal liabilities.
The coordinator binds exact source row hashes; standalone row shape alone does
not prove arbitrary replacement code has valid economics.

Opening must have finalized and every admitted initial currency synchronized
before capture. An unreadable currency can block this handoff; independent LP
parking/terminal return does not make that currency payable. Import never
reopens sale/grace. See [exact allocation](EXACT_ROYALTY_ALLOCATION.md).




This is the implementation and operating reference for the undeployed handoff
candidate. It is not release approval. The [central Todo](../TODO.md#task-security-chain-recovery)
owns remaining work; the [canonical migration design](CANONICAL_MIGRATION_DESIGN.md) records deferred
future-chain questions, not an implemented transport. Current schema/profile
evidence is linked from [features](IMPLEMENTATION_STATUS.md) and the
[report index](../reports/README.md); older handoff/native reports retain their
original source scope. **Production NOT APPROVED.**

## Supported boundary

The current coordinator binds
`SCHEMA = keccak256("ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_V9")`, matching
fresh accounting7 eight-word local Positions and LP-only fee intake1. Both peers must
expose this exact schema. Older WETH/native V1/V2/V3/V4 codecs are rejected, not
reinterpreted. Native ETH is asset zero; every admitted principal, reserve and
reward currency remains explicit. Current Positions contain no remote location
or composition-epoch fields. See [the profile](POSITION_V7.md). Matching wire schema is necessary, not proof
that a proposed different-code successor is economically compatible.

The candidate transfers the collection and classified economic state to one
replacement **on the same chain, before collective LP exit starts**. Every
nonempty bucket must be parked at Vault, every physical main/residual closed,
`LiquidityManager.activeSecondaryCount()==0`, and every draw complete. The retained principal V6-format
wire carries classified parked backing, not a live residual association. Once
`lpExitStarted` is set, preparation/transition/freeze are permanently blocked,
even after all holder payouts: this importer does not carry terminal principal
liabilities or authorize reopening LP. No external principal/royalty custody
request exists. [Holder exit](HOLDER_COLLECTIVE_EXIT.md) is a separate terminal path.

This release has no integrated bridge, remote ledger or cross-chain canonical
activation, and no operator-custody address can move funds externally. A future-chain protocol would
need separately reviewed transport, verified finality and replay/ownership
boundaries; post-halt recovery is deferred. There is no multisig-only or timeout
override. Same-chain retirement/activation is atomic: a reorganization reverts
both. Consumers still wait for the selected finality policy. Sealed implementations
cannot acquire missing code by changing configuration.

## Fixed modules and authority

[ZZZCanonicalHandoff](../src/ZZZCanonicalHandoff.sol) coordinates six state domains:
NFT, Vault, membership, LP rewards, royalty rewards and LP-only fee reserves.
The [NFT](../src/ZZZNFTCanonical.sol), [Vault](../src/ZZZVaultCanonical.sol) and
[Fees](../src/ZZZFeesCanonical.sol) companions are separately deployed, bound once
and checked against their owners at sealing. The new [RewardsCanonical](../src/ZZZRewardsCanonical.sol) is constructor-created and immutable in Rewards; coordinator slot3 binds that child and verifies its parent, Access and LP-allocation1. Funds stay in Rewards outside authenticated funding legs. They keep codecs outside the
custody contracts to meet normal EVM code-size limits. They have no configurable
executor, delegatecall, general withdrawal or arbitrary call facility.

The wallet returned by `Access.governance()` directly authorizes preparation,
freeze, commit, abort and reopening after a fully restored abort. There is no
timelock, scheduler or generic controller executor. Anyone can settle the next
captured domain, relay bounded records or advance an exact funding leg.
Relay callers cannot choose owners, balances or recipients.
The guardian pause is separate; unpausing cannot reopen a frozen or retired
canonical deployment. The bootstrap must prepare a destination as an inert
importer before sealing it. Its modules cannot be changed afterward.

The reviewed deployment commitment binds the controller, coordinator, sealed
modules and economic helper code/addresses. A code hash identifies the reviewed
implementation; it does not prove that arbitrary successor code is safe.
The user explicitly accepted this governance trust on 2026-10-17: reviewed
replacement code may differ from the source implementation. There is no on-chain
same-implementation restriction. Governance admission and independent review of
compatible successor economics remain necessary; a malicious approved replacement
could divert LP despite the source's exact-transfer checks. This accepted authority
does not authorize a finality, backing or source-retirement override.

## Sequence and point of no return

| Step | Source | Replacement |
| --- | --- | --- |
| Prepare destination | Still operates. | Bootstrap binds modules, calls `prepareImport(sourceController)`, configures dependencies and seals. Importer remains inert. |
| Announce | Governance-approved `startPreparation` names the already sealed importer and exact deployment/review commitments. New work stops; claims, transfers, reveal and permitted drains remain. | Bound to this source only. |
| Drain and freeze | Reveal all existing mints and park every funded LP, then governance-approved `freeze`; `lpExitStarted` must remain false. Global state changes before any balance observations. | Receives the source handoff identity and domain sizes. |
| Settle cutoffs | Phase 8 keeps all rights frozen. Six ordered, permissionless `settle(slot)` calls finalize only the captured amounts; retries cannot repeat a domain. Only completion changes the source to exportable phase 1. | Remains inert; no import or funding can proceed yet. |
| Export/import | `exportRows` commits complete settled domains in batches of at most eight. | `importRows` verifies each exact source record and builds the same rolling roots. Imported ownership and claims remain disabled. |
| Fund | Each one-use leg transfers the exact captured asset into its fixed peer module/companion first. Principal and each reward/reserve class stay separate. | The coordinator verifies the actual receipt, then calls `canonicalAccept` with zero `msg.value`. Companions forward already-funded ETH once; prefunds cannot replace a funding leg. |
| Commit | Governance checks all legs and roots, permanently retires the source. | In the same transaction, validates complete records/backing and activates once. Any failure rolls back both transitions. |

Exports include zero rows and the complete finite domain, rather than a relay's
chosen Merkle snapshot. Existing IDs, mint ordinals, owners, traits, quota/draw
inventory, VRF provenance, shares, activation, exact LP pending/phase/direct books, exact whole
royalty entitlements, reserves, admitted assets and protected unallocated balances
survive. Historical request namespaces stay authenticated. V9 requires the sale
and one-hour opening to be complete and imports that closed end; unused draw
inventory is preserved for integrity, not permission to mint again. Neither
replacement activation nor changing future mint-price policy reopens the sale.
Operator approvals are deliberately not imported. Existing minted IDs retain
the original collection/Vault identity; current custody routing is remapped to
the replacement. Ordinary holder redemption remains unavailable;
a later collective LP shutdown requires its separate governance action.

## Workflow size and relay budget

Small batches bound one call, not the complete handoff. Count the actual minted
NFTs `N`, permanently registered buckets `B` (including reservations), lifetime
pool aliases `L`, admitted LP currencies `A` and royalty currencies `R` at freeze.
Four bucket slots do not cap `L`; same-pair moves can add aliases over time.

| Ordered domain | Exact rows |
| --- | --- |
| NFT | `1001 + N` (fixed draw inventory plus minted rows) |
| Vault | `1 + B + L + N + A` |
| Membership | `1 + N` |
| LP rewards | `1 + A + N + K`, where `K=2023` if `N>0`, otherwise0 |
| Royalties | `1 + R + N * (1 + R)` |
| Fees | `1 + A + B * A` |

Read coordinator `recordCount(slot)` and each bound module's `canonicalCount()`
once captured and reconcile them to this
schema; a future different codec requires its own calculation. Total rows are
`1006 + 5N + NR + 3A + AB + B + R + L + K`. With separate direct calls and
maximum eight rows per export/import, those two phases need at least
`2 * sum(ceil(domainRows / 8))` calls, plus `3A+R` funding legs, freeze,
six settlements, completeImport and commit. Zero-value legs still need their
authenticated acknowledgment. Preparation, parking, deployment, confirmation
waits, receipts and retries are additional work.

For `N=1000, B=1, L=1, A=2, R=1`:9040rows,2268export/import calls,7funding legs
and 9control calls, or2284direct calls before those additional operations.
These are function-call counts, not measured gas, guaranteed transaction counts
or target-chain qualification; a reviewed batching relay would need separate
simulation and gas bounds. Rehearse the actual dimensions and abort budget
before freezing. Preserve cursors, roots and backing; do not omit history or
increase batch limits just to reduce the estimate. No silent lifetime-alias cap
or emergency import override exists.

### LP V9 record order

The LP child exports header8words, asset10words, NFT seed8words and raw node31words. Tree0 is equal collective; trees1–4 follow captured bucket order, each with ETH/ZZZ books. Seed ALL minted ordinal weights and direct credits before restoring pending/high/low nodes. Do not flatten claimables and then import the old phase: that changes future rights. Every asset reconciles direct liabilities, per-tree outstanding and actual backing; prefunds cannot substitute. The2023node domain omits only permanently unused tree padding. It needs253node pages even with one minted NFT; target transaction/page gas and full handoff/abort budget remain unqualified. See [exact layout](POSITION_V7.md).

## Backing, cutoffs and late receipts

Freeze captures every admitted ledger and classified fee-reserve balance before
settling any domain. Settlement is split into bounded domain calls, while the original cutoffs
remain immutable across blocks and operator outages. Only the captured pending
amount is allocated under the frozen membership.
Subsequent plain transfers cannot change the export root or substitute for a
captured obligation. Native Vault principal/quarantine, native Fees reserves, native
individual/collective whole-unit books and converted credits, and native royalties are
separate custody/accounting domains. Native currency remains a single admitted asset per applicable ledger. LP pending/phase/direct books and royalty whole-unit liabilities are carried exactly; converted ETH is not earned twice. The governed maintenance budget (default 3%, maximum 10%) does not haircut
claims or reserves. This direct handoff uses exact token units without conversion.

Unassigned source-companion donations are not exported or stored as new per-asset
freeze baselines. On abort, the fixed coordinator verifies an exact incoming balance
increase before the companion restores only that amount, preserving unrelated
prefunds. Importer acceptance separately retains its own pre-funding baseline.
This avoids allowing dust donations to add source freeze storage work.

Destination donations remain unassigned/quarantined; pre-activation receipts
cannot become retroactive rewards. The retired royalty ledger can still receive
marketplace payments. Its permissionless `forwardLate(asset)` sends only a
previously admitted currency to the fixed immediate successor; forwarding does
not recurse across a chain of replacements. An unadmitted new ERC20 sent after
retirement has no admission or generic rescue path. Inventory cached receivers,
currencies and pending orders before cutover. Creator inboxes and remote fee
intake do not exist in the current candidate. Unknown unsolicited tokens do not
expand its bounded handoff inventory.

## Cancellation and recovery

Before freeze, the existing exact-notice cancellation restores ordinary operation.
After freeze, including partial settlement/funding, `abort` permanently cancels
the importer. Every leg that actually left must return in exact units; retries
cannot return it twice. Native return funding first reaches the source companion,
then `canonicalRestore` receives a zero-value acknowledgment and forwards that
already transferred amount. It must not demand another copy of ETH as `msg.value`.
Unfunded legs are not fabricated, and source/destination prefunds remain separate.
`finishAbort` checks all returned legs and module backing before reopening source
rights. Successfully settled cutoff accounting remains settled. No timeout,
administrator balance edit or emergency principal withdrawal bypass exists.

After source retirement, abort and source reopening are impossible. The active
replacement can later prepare another reviewed same-chain replacement; old
deployments remain retired. Losing an asset dependency during a partially funded
handoff can keep rights frozen until exact restoration is possible. No universal
recovery promise is made for a broken or malicious token.

### Recover receipts sent to a cancelled importer

An aborted destination stays permanently cancelled; it cannot reopen or pay its
inert imported NFT accounting. After `finishAbort()` has restored every funded
leg, its coordinator can return remaining royalty receipts to the authenticated
current canonical royalty receiver. This is a separate reviewed **current-weight**
allocation, not an override of the aborted import or a reconstruction of past
receipt-time entitlements. It never sends principal or funds to a chosen wallet.

1. Read `cancelledRoyaltyReturnController()` on the **cancelled** coordinator. It
   initially resolves to its original source. That source must be operating or
   retired, proving abort restoration completed. While it remains frozen/aborting,
   no recovery is permitted.
2. If the resolved controller has since retired, call
   `advanceCancelledRoyaltyReturn()` once per completed successor hop. Anyone may
   submit this bounded metadata-only call; there is no target argument. A hop
   compares its immutable original import chains with the retired source's frozen
   export chains through the existing fixed Vault companion's read-only check. A successor currently frozen/importing must first finish or
   abort its later handoff. Later changes to its current snapshot do not erase its
   original import proof. Repeat until the resolved controller is operating.
3. The current target must be sealed, unpaused, outside preparation, with an open
   royalty window and a positive active cohort. Admit the exact currency there
   first if necessary. Review the cancelled receiver's actual balance, target,
   receiver and current active weights; record a nonzero `bytes32 reviewHash`.
   This hash records the review; it does not prove token safety or bind a live
   snapshot by itself.
4. From the **target's current governance wallet**, call the cancelled
   coordinator's `recoverCancelledRoyalties(asset, reviewHash)`. Use the zero
   address for native ETH, otherwise the exact ERC20 address. Send no ETH value.
   The function syncs the target, transfers all remaining physical units of that
   currency from the cancelled royalty receiver, and syncs again. Those units
   accrue to the captured current active weights; preexisting target unallocated
   balances remain separate. Holders then use normal original-currency claims.
5. Re-read balances and receipts. A later receipt at the cancelled address needs
   another reviewed recovery. Authority, lifecycle, target or membership changes
   during callbacks revert the entire operation. Taxed, rebasing, blocked or
   otherwise incompatible tokens may still fail; there is no universal sweep.

`CancelledRoyaltyReturnAdvanced` and `CancelledRoyaltiesRecovered` record routing
and movement. Count the target's actual credited receipt once, never movement as
additional income. These functions do not revive the cancelled NFT collection,
change old earned liabilities, bypass abort backing, swap assets or reopen LP.
Target-chain gas, provider and operating qualification remain separate release work.

## Integration and qualification

Fresh API/keeper profiles explicitly select accounting7, custody5, portfolio2,
maintenance3/confirmation3/Budget4/LP routing2 and fee intake1,
and verify `Vault.ACCOUNTING_VERSION()` plus reviewed runtime pins. Legacy WETH profiles and
predecessor epochs retain their own currency/version interpretation; saved nonce,
receipt and pending journals cannot be reset or reinterpreted as a native upgrade.
Historical native2/accounting3/accounting4 artifacts cannot serve accounting7 merely
by relabeling a manifest. Accounting7 website/service acceptance remains open; public
DEPLOYMENT is null, signing stays Anvil-only and existing fixtures are unchanged.

Keeper reads `canonicalState()` strictly and stops all new transaction submissions
while frozen, importing, retired or cancelled; it continues recovery of already
submitted receipts. The old isolated staging service has not been upgraded.

API/indexer/frontend integration must expose lifecycle and successor identity,
stop presenting a retired source as active, follow complete deployment lineage
for lifetime claimed totals, and distinguish imported `Transfer` events from new
mint sales. Marketplace collection recognition and source retirement notices
also need rehearsal. Export relaying, gas at the complete admitted asset
domain, target-chain operation, qualified successor templates and independent
audit remain release work. A local handoff test is not cross-chain qualification.

Import preserves a contract owner's address without calling ERC721 receiver
callbacks. An escrow hardcoded to the old collection may be unable to release
the replacement NFT even on the same chain. Contract-owner compatibility and
marketplace escrow cutover therefore require review before approving a handoff;
preserving an address alone does not prove recoverable ownership. Use the implemented
[confirmed holder inventory](HOLDER_PREFLIGHT.md), resolve flagged contracts before
freeze, and rescan frozen ownership before final review. It reports gaps and never
automatically approves release compatibility.

## Operator policy for pending reveals

The selected policy is qualified/funded provider operations plus stopping new
minting and finalizing every existing draw before freeze. Use [the operator
manual](OPERATOR_MANUAL.md#whole-collection-replacement) and the read-only
`/v1/mint-readiness` observation. No pending-request carry/reroll path is selected.
An unanswered original request still blocks this replacement; postpone/cancel
preparation and resolve it with the original provider. Ordinary LP pool migration
has no reveal-completion requirement. Collective holder return also does not
require completed reveals, and permanently disables this canonical path. Escrow compatibility requires separate
rehearsal before freeze; no owner rewrite is authorized.
