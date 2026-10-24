# Canonical handoff: same-chain implementation

This is the implementation and operating reference for the undeployed handoff
candidate. It is not release approval. The [central Todo](../TODO.md#task-security-chain-recovery)
owns remaining work; the [canonical migration design](CANONICAL_MIGRATION_DESIGN.md)
retains the wider future-chain requirements. Source-bound verification belongs in
[the native candidate report](../reports/native-eth-port/VERIFICATION.md).
Earlier [handoff evidence](../reports/canonical-handoff/VERIFICATION.md) retains
its original source/accounting scope.

## Supported boundary

The V2 coordinator binds
`SCHEMA = keccak256("ZZZ_CANONICAL_SAME_CHAIN_NATIVE_V2")`. Both source and
replacement must expose that schema; V1 WETH-accounting deployments are rejected,
not silently reinterpreted. Native ETH is asset zero. All admitted assets,
including native backing and historical compound, remain explicit currencies.
Each Vault group carries its authenticated `uint64 compositionEpoch`; parked
idle follows the actual current pair while original home identities survive.

The candidate transfers the collection and classified economic state to one
replacement **on the same chain**. Every nonempty bucket must first be parked
at the home Vault, every draw must be complete, and principal/royalty external
custody must be fully resolved. The retired LP bridge/pair executor stack cannot
be bound to this candidate; historical records do not qualify remote closure.

Cross-chain canonical activation, authenticated channel closure and obligation
funding, transport, replay boundaries and post-halt recovery remain unimplemented.
There is no multisig attestation or timeout override. Same-chain source retirement
and replacement activation are atomic: a reorganization reverts both. Off-chain
consumers must still wait for the selected finality policy. These missing code
capabilities cannot be added to already sealed implementations.

## Fixed modules and authority

[ZZZCanonicalHandoff](../src/ZZZCanonicalHandoff.sol) coordinates six state domains:
NFT, Vault, membership, LP rewards, royalty rewards and fee reserves/inboxes.
The [NFT](../src/ZZZNFTCanonical.sol), [Vault](../src/ZZZVaultCanonical.sol) and
[Fees](../src/ZZZFeesCanonical.sol) companions are separately deployed, bound once
and checked against their owners at sealing. They keep codecs outside the
custody contracts to meet normal EVM code-size limits. They have no configurable
executor, delegatecall, general withdrawal or arbitrary call facility.

The existing governance controller authorizes preparation, freeze, commit, abort and reopening
after a fully restored abort. Anyone can settle the next captured domain, relay the bounded records or advance an
exact funding leg. Relay callers cannot choose owners, balances or recipients.
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
| Drain and freeze | Reveal all existing mints, resolve plans, return/park custody, then governance-approved `freeze`. Global state changes before any balance observations. | Receives the source handoff identity and domain sizes. |
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
remapped to the replacement. No NFT principal becomes redeemable.

## Backing, cutoffs and late receipts

Freeze captures every admitted ledger and inbox balance before settling any of
them. Settlement is split into bounded domain calls, while the original cutoffs
remain immutable across blocks and operator outages. Only the captured pending
amount is indexed under the frozen membership.
Subsequent plain transfers cannot change the export root or substitute for a
captured obligation. Native and wrapped inbox balances are captured separately.
Native Vault principal/quarantine, native Fees reserves/inbox protection, native
individual/collective indices and converted credits, and native royalties are
separate custody/accounting domains. Receiver asset zero is not duplicated in an
extra native protection slot. LP and royalty liabilities, including division dust
and per-NFT fractions, are carried exactly; converted ETH is not earned twice. The local 3% principal execution budget is not a haircut of
claims or reserves. This direct handoff uses exact token units with no conversion.

Unassigned source-companion donations are not exported or stored as new per-asset
freeze baselines. On abort, the fixed coordinator verifies an exact incoming balance
increase before the companion restores only that amount, preserving unrelated
prefunds. Importer acceptance separately retains its own pre-funding baseline.
This avoids allowing dust donations to add source freeze storage work.

Destination donations remain unassigned/quarantined; royalty and creator inbox
receipts before destination activation cannot become retroactive rewards. Old
marketplace royalty receivers and creator inboxes can still receive payments.
Permissionless late forwarding sends them to the one immediate successor; it
does not recurse through an arbitrary chain of replacements. Creator receipts
remain unsplit until processed under the active deployment, so 80/10/5/5 is not
applied twice. Queued local creator funds block new membership until processed.
Unknown unsolicited tokens do not create an unbounded migration inventory.

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

Fresh native API/keeper profiles explicitly select accounting version 2 and verify
`Vault.ACCOUNTING_VERSION()` plus reviewed runtime pins. Legacy WETH profiles and
predecessor epochs retain their own currency/version interpretation; saved nonce,
receipt and pending journals cannot be reset or reinterpreted as a native upgrade.
The current website V2 profile still requires qualification; public deployment
remains null, shared browser signing Anvil-only and the existing 8902 fixture is unchanged.

Keeper reads `canonicalState()` strictly and stops all new transaction submissions
while frozen, importing, retired or cancelled; it continues recovery of already
submitted receipts. The old isolated staging service has not been upgraded.

API/indexer/frontend integration must expose lifecycle and successor identity,
stop presenting a retired source as active, follow complete deployment lineage
for lifetime claimed totals, and distinguish imported `Transfer` events from new
mint sales. Marketplace collection recognition and source retirement notices
also need rehearsal. Export relaying, gas at the complete admitted asset/inbox
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
has no reveal-completion requirement. Escrow compatibility requires separate
rehearsal before freeze; no owner rewrite is authorized.
