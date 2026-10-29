# Canonical handoff: same-chain implementation



This is the implementation and operating reference for the undeployed handoff
candidate. It is not release approval. The [central Todo](../TODO.md#task-security-chain-recovery)
owns remaining work; the [canonical migration design](CANONICAL_MIGRATION_DESIGN.md) records deferred
future-chain questions, not an implemented transport. Current schema/profile
evidence is linked from [features](IMPLEMENTATION_STATUS.md) and the
[report index](../reports/README.md); older handoff/native reports retain their
original source scope. **Production NOT APPROVED.**

## Supported boundary

The current coordinator binds
`SCHEMA = keccak256("ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5")`, matching
accounting4 eight-word local Positions and LP-only fee intake1. Both peers must
expose this exact schema. Older WETH/native V1/V2/V3/V4 codecs are rejected, not
reinterpreted. Native ETH is asset zero; every admitted principal, reserve and
reward currency remains explicit. Current Positions contain no remote location
or composition-epoch fields. See [the profile](POSITION_V4.md).

The candidate transfers the collection and classified economic state to one
replacement **on the same chain, before collective LP exit starts**. Every
nonempty bucket must be parked at Vault and every draw complete. Once
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
and checked against their owners at sealing. They keep codecs outside the
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
inventory, VRF provenance, shares, activation, reward indexes, paid checkpoints,
fractions, reserves, admitted assets and quarantine classifications survive.
New VRF requests use a new namespace, preserving historical request provenance.
Operator approvals are deliberately not imported. Existing minted IDs and later
mints use the original collection/Vault identity; current custody routing is
remapped to the replacement. Ordinary holder redemption remains unavailable;
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
| LP rewards | `1 + A * (1 + B + N)` |
| Royalties | `1 + R + N * (1 + R)` |
| Fees | `1 + A + B * A` |

Read coordinator `recordCount(slot)` and each bound module's `canonicalCount()`
once captured and reconcile them to this
schema; a future different codec requires its own calculation. Total rows are
`1006 + 4N + N(A+R) + 3A + 2AB + B + R + L`. With separate direct calls and
maximum eight rows per export/import, those two phases need at least
`2 * sum(ceil(domainRows / 8))` calls, plus `3A+R` funding legs, freeze,
six settlements, completeImport and commit. Zero-value legs still need their
authenticated acknowledgment. Preparation, parking, deployment, confirmation
waits, receipts and retries are additional work.

For `N=1000, B=1, L=1, A=2, R=1`:8019rows,2012export/import calls,7funding legs
and9control calls, or2028direct calls before those additional operations.
These are function-call counts, not measured gas, guaranteed transaction counts
or target-chain qualification; a reviewed batching relay would need separate
simulation and gas bounds. Rehearse the actual dimensions and abort budget
before freezing. Preserve cursors, roots and backing; do not omit history or
increase batch limits just to reduce the estimate. No silent lifetime-alias cap
or emergency import override exists.

## Backing, cutoffs and late receipts

Freeze captures every admitted ledger and classified fee-reserve balance before
settling any domain. Settlement is split into bounded domain calls, while the original cutoffs
remain immutable across blocks and operator outages. Only the captured pending
amount is indexed under the frozen membership.
Subsequent plain transfers cannot change the export root or substitute for a
captured obligation. Native Vault principal/quarantine, native Fees reserves, native
individual/collective indices and converted credits, and native royalties are
separate custody/accounting domains. Native currency remains a single admitted asset per applicable ledger. LP and royalty liabilities, including division dust
and per-NFT fractions, are carried exactly; converted ETH is not earned twice. The governed maintenance budget (default 3%, maximum 10%) does not haircut
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

## Integration and qualification

Fresh API/keeper profiles explicitly select accounting version4, custody3 and fee intake1,
and verify `Vault.ACCOUNTING_VERSION()` plus reviewed runtime pins. Legacy WETH profiles and
predecessor epochs retain their own currency/version interpretation; saved nonce,
receipt and pending journals cannot be reset or reinterpreted as a native upgrade.
Historical native2/accounting3 website artifacts cannot serve accounting4 merely
by relabeling a manifest. Accounting4 website/service acceptance remains open; public
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
