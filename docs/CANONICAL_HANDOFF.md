# Canonical handoff: same-chain implementation

This is the implementation and operating reference for the undeployed handoff
candidate. It is not release approval. The [central Todo](../TODO.md#task-security-chain-recovery)
owns remaining work; the [canonical migration design](CANONICAL_MIGRATION_DESIGN.md)
retains the wider future-chain requirements. Source-bound verification belongs in
[the handoff report](../reports/canonical-handoff/VERIFICATION.md).

## Supported boundary

The 2026-10-23 local composition extension appends a `uint64 compositionEpoch`
to each Vault group record. Successors import that authenticated epoch and
classify parked idle by the current pool's accounting pair, preserving original
home currency identities. Both reviewed deployments must support this record
format; old-format bytes are not silently accepted. See [pair-conversion
accounting and verification](PAIR_MIGRATION.md). This does not enable V3 principal
bridging of a composed bucket or complete cross-chain canonical relocation.

The candidate transfers the complete collection and classified economic state to
one replacement **on the same chain**. All nonempty LP buckets must first be
parked at the home Vault; every minted NFT must be revealed. The initial path
rejects any source whose legacy bridge has sent or received messages. A zero
current remote balance cannot prove that historic channels are closed.

Cross-chain canonical activation, channel closure proofs, historical v3 replay
cutoffs, cross-chain obligation funding and post-halt recovery are not supplied.
There is no multisig attestation or timeout override. Same-chain source retirement
and replacement activation occur atomically: a reorganization reverts both.
Off-chain consumers must still wait for the chain's selected finality policy.
An imported replacement cannot initiate legacy v3 principal bridging because v3
conflates original bucket identity with current canonical routing. This explicit
restriction must be resolved with a reviewed message/lineage version before
future-chain qualification. These capabilities cannot be added to sealed code.

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
| Fund | Each one-use leg sends the exact captured asset amount to its fixed peer module. Principal and each reward/reserve class stay separate. | Measured receipt plus module acceptance; prefunds cannot replace authenticated funding. |
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
LP and royalty liabilities, including division dust and per-NFT fractions, are
carried exactly. The local 3% principal execution budget is not a haircut of
claims or reserves. This direct handoff uses exact token units with no conversion.

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
After freeze, including partial settlement, `abort` permanently cancels the importer. Every leg that actually
left the source must return in exact units; retries cannot return it twice.
`finishAbort` checks all returned legs and module backing before reopening source
rights. Successfully settled cutoff accounting remains settled. No timeout,
administrator balance edit or emergency principal withdrawal bypass exists.

After source retirement, abort and source reopening are impossible. The active
replacement can later prepare another reviewed same-chain replacement; old
deployments remain retired. Losing an asset dependency during a partially funded
handoff can keep rights frozen until exact restoration is possible. No universal
recovery promise is made for a broken or malicious token.

## Integration and qualification

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
