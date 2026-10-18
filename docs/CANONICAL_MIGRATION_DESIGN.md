# Whole-protocol canonical migration design

Design direction recorded 2026-10-17. The current candidate implements a
[same-chain handoff](CANONICAL_HANDOFF.md): freeze, complete bounded export/import,
exact backing, cancellation and atomic single-successor activation. **Cross-chain
canonical handoff remains unimplemented.** This document retains its wider design
requirements; proposed proof/transport mechanisms below are not current functions.
Reversible timelocked preparation has its own [scope and permitted draining](MIGRATION_SAFETY.md).
The [central Todo](../TODO.md) owns implementation progress; the
[architecture review](ARCHITECTURE_EVOLUTION.md) records the wider decisions.
The release decision remains **NOT APPROVED**.

The user selected a controlled whole-protocol migration **while the original
canonical chain still works**. Recovery after an irreversible chain halt is
deferred. The user additionally requires **verified finality, with no multisig-only
override**. A reviewed proof must authenticate finalized source retirement before
successor activation; a vote, timeout or transport send receipt is insufficient.
This does not select a particular verifier, successor implementation or operating
parameter. Unsupported destinations must remain unavailable until qualified.

Here, **successor** means the replacement PoPL deployment that takes over the
collection's NFT ownership, LP allocations and reward balances. For example,
PoPL contracts on Ink could replace the original deployment on Robinhood.
Only one deployment may provide those economic rights for a given migrated state;
the replacement must verify the old deployment's finalized retirement before
activating them, preventing duplicate ownership or claims across both chains.

## What moves, and what must remain fixed

LP migration moves a bucket's custody. Canonical migration also transfers the
authority that answers who owns each NFT and who may claim both reward ledgers.
Creating another ERC721 collection or copying a balance snapshot does not disable
the original rights and cannot establish a safe canonical successor.

The migration must preserve the 1,000-NFT cap, existing token IDs, owners and
immutable traits; exact rarity/artwork inventory; NFT shares and bucket lineage;
activation and royalty eligibility; both complete reward ledgers; backed reserves
and their classifications; and a single canonical authority at every epoch.
It must preserve fixed 80/10/5/5 LP allocations, equal activated-NFT collective
membership, 5% requested marketplace royalties and royalty weights 1/2/3.
No principal redemption, administrator NFT transfer or arbitrary call is added.

An approved arbitrary successor could still implement malicious economics.
Code hashes and timelocks identify and delay that choice; they do not prove that
new code honors these rights. Admissible implementation templates and the
verification/admission policy must be reviewed before deployment. On2026-10-17,
the user explicitly allowed governance to approve different reviewed replacement
code through the timelock, accepting that trust instead of an identical-code rule.
This is a constrained protocol-evolution authority, not an immutability guarantee
under unrestricted governance replacement.

## Capabilities must exist before sealing

The current [controller](../src/ZZZAccessController.sol) permanently fixes module
addresses at `seal`. The NFT, LP and royalty ledgers now enforce canonical lifecycle
guards and fixed export/import interfaces. The same-chain coordinator carries
their complete state and classified backing. Operational pause still deliberately
leaves claims available; the separate canonical freeze disables them until exact
restoration or replacement activation. The current v3 bridge protocol preserves
the original home identity and cannot carry cross-chain canonical migration.
The supported path therefore rejects historic bridge activity and prevents an
imported successor from initiating legacy v3 principal sends.

The remaining cross-chain state machine, verified-finality/transport boundaries,
lineage version and late-receipt compatibility must be implemented and audited
**before the initial deployment is sealed**. A future compatible LP destination
does not retrofit these abilities into the original NFT or ledgers.

## Identity and epoch model

Use two distinct concepts in a future implementation:

| Identity | Rule |
| --- | --- |
| Collection origin | Permanent genesis chain, NFT/Vault identity and deployment domain. |
| NFT identity | Existing uint256 ID and mint ordinal are unchanged. Remaining unminted IDs must use a reviewed continuous origin/ordinal domain, not accidentally collide or restart at the successor. |
| Bucket lineage | Existing bucket ID and original home-pool derivation remain permanent. A migration must not hash a replacement bucket and silently move NFT shares into it. |
| Canonical authority | A monotonically increasing canonical epoch binds the current NFT, ledgers, Vault, controller, chain and exact deployment/code identities. |
| Custody composition/location | Pool, venue, assets and physical custody are separate from genesis lineage and canonical ownership authority. |
| Handoff identity | Hash binds protocol version, origin, source/destination epochs and endpoints, source finalized state commitment, asset manifest, successor configuration and nonce. |

Each retired epoch may commit to **one immediate successor only**. The successor
can later perform the same reviewed protocol to another epoch; this does not
reopen older epochs. All migration messages, receipts, proofs, imports and late
funding envelopes require the complete domain. Equal numeric chain IDs, token
addresses, token symbols or a copied contract ABI do not prove identity.

The current `homeChain/homeVault/homeReceiver/homeToken0/1` fields mix immutable
lineage with live routing. A new version must separate those roles explicitly.
Rewriting them in place would break historical reward paths and return checks.

## Conservative baseline: drain before freezing

The initial design should require a fully observed, settled starting state:

- Stop new mints and new migration/strategy/configuration operations during the
  announced preparation window. Keep ordinary transfers and funded claims
  available until the exact freeze, with their final state exported afterward.
- Fulfill and finalize **every already minted NFT**, strictly in the existing
  mint order. No pending VRF request or unrevealed mint may cross the baseline
  freeze. No retry, administrator word, trait selection or reroll is inferred.
- Settle pending admitted royalty receipts and creator inbox receipts under the
  pre-freeze membership. Settle fee dust and remote funded-accounting barriers.
- Complete or authentically cancel all pending principal/reward/ACK operations;
  resolve out-of-order delivery and frozen source plans. A timeout is not proof
  that no packet can arrive. Stop new sends before defining channel cutoffs.
- Prefer returning each bucket to the functioning home chain and parking its
  principal before whole-protocol export. This avoids silently reauthorizing
  remote custody through an unrelated ownership migration. If that cannot be
  achieved, a separately specified satellite handoff/acknowledgement protocol is
  required; copying the home snapshot is insufficient.

Draining does not require all 1,000 NFTs to have been sold. If supply is below
1,000, every existing mint must be revealed and the remaining exact rarity and
artwork inventory must be carried. If the fixed VRF service cannot complete an
earlier reveal, this conservative migration cannot proceed. A continuity/fallback
policy would be a separate decision, not an emergency permission invented here.

The pre-freeze settlement cannot prevent later plain transfers into old inboxes.
Those are handled through the explicit post-cutoff mechanism below, not ignored.

## Bounded state machine and cross-chain requirements

Announced preparation and the same-chain Frozen/exporting, staged, terminal and
active states are implemented in the candidate. The table describes the broader
cross-chain requirements too: source retirement and destination activation there
need separate finalized proofs. Preparation does not authenticate satellite drain.

| State | Source authority and permitted work | Destination state |
| --- | --- | --- |
| Operating | Existing rights and ordinary guards. | No canonical authority. |
| Announced | Exact successor proposal, review material and public notice; new mutation classes stop as specified above. Cancellation remains safe. | Reviewed deployment may be prepared, but cannot mint economic substitutes, claim, transfer imported NFTs or spend staged principal. |
| Frozen/exporting | Transfers, minting, activation/top-ups, claims, ordinary ledger synchronization/index changes, asset admission and conflicting governance/keeper operations stop at the canonical-state level. Only captured-cutoff settlement, bounded export and exact custody staging are allowed. | Imports are inert and replay protected. |
| Staged/ready | Source stays frozen. Its on-chain commitment is complete; destination proves exact imported state and full classified backing. | All required roots/counts and asset funding gates verified. No claims or transfers yet. |
| Terminal committed | One successor and state commitment become irreversible after authenticated readiness. Old claims, transfers, minting and ordinary accounting can never reopen. | Awaits proof of finalized source terminal commit; no timeout activation. |
| Successor active | Source is a retired lineage/late-funding forwarder only. | Activates the exact funded state once, then ordinary rights belong to this epoch. |

The freeze is a protocol-wide lifecycle control separate from the guardian pause
bit. It is reversible only through the proved pre-terminal abort path below;
terminal commit is irreversible. Neither ordinary unpausing, rotating a keeper
nor executing an old queued timelock call may bypass it. Direct claims, router claims, transfer variants, callbacks,
permissionless sync and all accounting entrypoints must enforce it consistently.
No user-controlled recipient, USD assertion, raw call or rescue selector is part
of export or funding. Exact code/configuration pins and fixed typed destinations
apply to every handoff leg.

### Immutable receipt cutoff before multi-transaction export

Stopping ledger writes does not stop plain ERC20/native payments. Freeze must
therefore atomically record an immutable cutoff vector for every admitted
ledger/inbox asset: observed raw balance, already-accounted liabilities/reserves,
protected prefunds and the resulting unprocessed admitted delta. Establish the
global freeze guard before those external balance observations so callbacks
cannot transfer NFTs, claim, change membership or bypass the cutoff. Capture
native and wrapped balances separately where an inbox normalizes them.

The exporter must not read a later moving `balanceOf`/`pending()` result as if it
were that snapshot. After capture, permit only one-time bounded settlement of the
**captured amount**, under the frozen pre-cutoff membership/share/royalty weights.
Then seal the resulting global indexes/classified backing and export the complete
state. Post-cutoff receipts are excluded from that settlement and from the base
funding manifest; they enter the separate authenticated late-funding stream.
Current all-pending `sync()` interfaces cannot be reused unchanged for this step.

Records need per-asset processed/exported flags and exact reserved base amounts so
a captured delta cannot be allocated or bridged twice, or also appear as late
gross revenue. Bound and benchmark the atomic cutoff across the full admitted
asset/inbox population before approving this design. If it cannot fit, design an
equivalently immutable, authenticated cutoff mechanism; do not silently switch
to an operator's snapshot or moving balance reads. A legitimate pre-terminal
abort retains correctly settled cutoff accounting and restores its exact backing
before source rights reopen.

### Cancellation and point of no return

Before freeze, cancel the announcement and restore ordinary operation. After
freeze but before any exported custody can be used, abort only through a reviewed
state transition that invalidates the staged epoch and preserves the exact source
state. Once funds have crossed chains, reopening the source requires finalized
proof that the destination is cancelled/inert, every relevant packet is resolved
and **all required backing has returned**. Elapsed time or an operator assertion
cannot establish this. Some failures will leave both sides safely frozen while
recovery waits for the selected proof/transport mechanism.

The **point of no return is the finalized source terminal commit**. After that,
the source never resumes canonical rights, even if activation is delayed or the
successor fails. Retrying the exact activation is allowed; approving a second
competing successor or restoring source claims is not. This deliberately favors
no duplicate ownership/claims over a false promise of recovery from every outage.

## Complete state commitment

A user-provided JSON/Merkle snapshot is not authoritative. Future source modules
must expose their actual state through fixed typed export views/operations after
freeze. Bounded permissionless progress computes or authenticates commitments
over a **complete finite domain**, with one record per index and explicit zero
records where needed. Anyone can relay source-authenticated records; nobody may
choose their content, owner, denominator or reserve category.

| Domain | Required committed state |
| --- | --- |
| NFT identity/ownership | Actual existing IDs in mint-ordinal order, owner, ordinal, minted flags/count and continuous Vault sequence. Balances are derived and checked, not separately trusted. Do not import operator approvals. |
| Traits/randomness | Revealed flag, rarity, palette, pattern/color and metadata base/inventory version; request/fulfillment provenance. Preserve rarityRemaining, remainingToReveal, nextToFinalize and sparse Fisher-Yates artworkDraw entries exactly. Duplicate-looking artwork is insufficient to reconstruct consumed inventory slots. |
| Future mints | Remaining quota and without-replacement inventory, unchanged cap/economics, reviewed destination VRF support. Historical request IDs remain provenance, not live callbacks. New requests need an epoch/coordinator namespace so a reused numeric request ID cannot collide or reroll an old mint. |
| Shares/membership | NFT->bucket mapping, per-NFT shares and contributionUSD; exact bucketTotalShares; activated eligibility and totalEligible. Reserved None and historical bucket slots/pool aliases remain admitted without inventing principal. |
| LP ledger globals | Admitted asset identities/order, index, ownerIndex per bucket/asset, liabilities, orphaned and reserved global division dust. |
| LP ledger per NFT/asset | individual, collective, paidIndex, fraction, paidOwnerIndex and ownerFraction. Do not replace this with rounded claimable() values. |
| Royalty globals | Native/ERC20 asset admissions/order, totalWeight, index, liabilities, accounted, orphaned and actual pending receipts at cutoff. |
| Royalty per NFT/asset | weightOf, accrued, paidIndex and fraction, including zero/dormant rows. |
| Vault/physical custody | Bucket lineage/location/composition, shares/deposit metadata, principal and attributed idle, exact actual fungible balances/LP ownership, totalIdle and permanent reservations. Principal is not reward backing. |
| Fees and reserves | Per-bucket/asset dust and compoundBalance, per-asset buybackBalance/accounted, all remote allocated/expected/received individual/collective counters and bound historical asset paths. Already burned ZZZ is historical evidence, not a transferable reserve. |
| Inboxes/quarantine | Exact creator receiver identities and protected prefunds/native amounts; known admitted quarantine/orphan balances; royalty prefunds; unsupported donations remain classified and cannot become reward/principal funding. |
| Messages | Domain/route/policy/code identities, custody epochs/location commitments, complete outstanding-operation reconciliation and historical replay/cancellation cutoffs. Old channel roots remain archived; the new canonical epoch rejects replay of old ordinary v3 packets. |

At most 1,000 NFT records, four historical local buckets, 32 LP assets and 17
royalty slots are current bounds; these are not a claim that all other historical
route/message mappings can be copied with one bounded loop. The new protocol must
track complete enumerable outstanding domains from genesis. A scalar nonce is
not proof that out-of-order or cross-channel packets have all settled.

## Full solvency before activation

For each admitted economic asset, reconcile the exact source custody classes and
their destination funding independently. At the destination:

`observed funded units >= imported liabilities + imported orphan/quarantine + other protected obligations`

Apply the correct classes per ledger/module; do not add or net principal against
reward reserves, use prefunds twice, count borrowed/donated tokens as authenticated
handoff funding, or infer solvency merely from the sum of rounded NFT claims.
Global division dust and per-NFT fractions survive. Destination funding uses exact
balance deltas and an authenticated one-use asset/obligation manifest, with
counterfeit, taxed and rebasing dependencies failing closed.

Funded LP and royalty liabilities preserve exact economic units. The user-approved
3% principal migration-conversion budget does **not** authorize a 3% haircut of
claims, orphan reserves or their backing. Funding/transport costs for those
obligations require a separately funded operating budget unless another explicit
policy is approved. Principal conversions use the aggregate migration budget;
activation/top-ups continue to use 1%. Returning home and forwarding to a successor
must not disguise multiple per-leg 3% allowances as one operation.

Cross-chain asset identity requires reviewed backing and units/decimals. Native
address zero on two chains does not prove the same economic asset. Source ETH
royalties may need an exact reviewed wrap/bridge representation; another chain's
native coin cannot simply replace ETH. If an existing admitted liability lacks a
safe fully funded destination representation, the baseline handoff is blocked.
No forced USD conversion of claims is inferred.

Known quarantined balances remain quarantined and cannot pay migration costs.
Unsolicited unsupported junk tokens cannot force an unbounded inventory scan or
require arbitrary transfers; their untouched legacy custody is disclosed. This
does not license sweeping legitimate admitted prefunds. Mint proceeds already
paid to the designated treasury are not protocol principal or migration backing.

## Same-chain and cross-chain activation proofs

For a same-chain replacement, stage the bounded state over multiple transactions
while frozen. Terminal commit and successor activation should then occur in one
atomic transaction using exact fixed-contract state/funding checks; failure rolls
both transitions back. Importing all 1,000 NFTs and 49 asset slots in that final
transaction is not required or assumed feasible. Current LP routes reject
same-chain endpoints, so this needs its own reviewed protocol.

For cross-chain replacement, there is no general atomic transaction. A concrete
two-way evidence model is required: source authenticates destination readiness,
and destination authenticates a finalized source terminal commit. Bind exact
epochs, chain IDs, deployment anchors, state/asset roots, code/configuration and
nonces. Reorganizations below the promised finality boundary cannot be wished
away with a confirmation count.

| Candidate evidence model | Additional assumption; not selected |
| --- | --- |
| Audited light-client/finality plus state proofs | Each chain has an implemented, funded and maintained verifier for the other's actual consensus/finality. Unknown future chains do not acquire this automatically. |
| Reviewed canonical messaging/bridge verification | Safety and liveness inherit that provider's actual authenticated-origin, validator/admin and finality assumptions. Code pins alone do not prove these properties. |
| Explicit threshold attestation with a dispute/review process | Adds an identified authority capable of attesting false state/finality. Quorum, independence, key rotation, evidence publication, challenge rules and failure handling require explicit approval. No new attestor is appointed here. |

An off-chain relayer may transport a valid proof but must not become the party
that decides its truth. The original chain must still be usable through export,
funding, terminal commit and finalized activation evidence. Post-halt checkpoint
recovery, administrator reconstruction and second-successor override are outside
the accepted scope.

## Bounded imports and lazy reward materialization

Do not require one holder to submit another holder's wallet signature or to claim
before migration. Import existing NFT identity/owner records permissionlessly
from authenticated source data. Destination transfers and economic actions stay
disabled until canonical activation. Imported owner contracts require explicit
compatibility review: the same address on another chain may be absent or different
code. Default ownership must not be reassigned to an administrator. Any
holder-authorized destination account mapping needs a separate scoped design and
approval; an inaccessible contract owner can block the baseline migration.

A practical design may import all bounded NFT/base records before activation,
while leaving asset-specific historical reward rows lazy under the authenticated
complete-state commitment. An NFT/asset row is initialized exactly once before
any claim/checkpoint that uses it. It restores exact accrued values, paid indexes
and fractions, then accrues the difference to current destination indexes. The
owner is checked against the **current destination NFT**, not the old snapshot
owner, so unclaimed rights still follow later transfers.

All shares, totalEligible, totalWeight and global/bucket indexes must be effective
for **the complete imported population from activation**. Counting only NFTs that
have materialized would let early users take other holders' rewards. Transfers do
not require settling all asset rows. Top-ups/membership changes must materialize
and checkpoint every row their accounting depends on before changing shares or
weights. Zero rows need authenticated inclusion/default rules; absence of a
record cannot be treated as an operator-chosen zero.

Provisional engineering batches for benchmarking are at most 16 base NFT records,
eight NFT/asset rows, or one authenticated asset-funding leg per transaction. These
are proposed limits, not qualified gas guarantees. The existing 32-operation claim
router does not prove that 32 new proof/import operations fit. Benchmark cold
worst-case nonzero rows, proofs, contract owners, callbacks and every admitted
asset under standard runtime/initcode and target-chain gas limits. Bound all
progress by explicit cursors/bitmaps and expose completion without scanning all
NFTs in an ordinary claim.

Data availability is part of safety: source-derived manifests/proofs must remain
publicly retrievable without a private API, with roots/counts and exact backing
independently reproducible. Missing proof data must never justify a guessed owner
or ledger reset. Protect materialization from replay, partial overwrite, duplicate
ordinal/ID, incorrect sums and attempts to initialize a row after it has changed.

## Legacy NFTs, marketplace royalties and late payments

The old NFT contract address cannot move to another chain. Its ERC2981 request
and cached marketplace listings may continue to direct 5% to the old receiver.
The new canonical NFT is a new chain/contract collection with preserved origin
and token IDs; marketplace recognition, metadata/redirect communication and old
listing retirement require rehearsal. Never claim that OpenSea automatically
replaces the collection or enforces royalty payment.

After source terminal commit, old NFTs remain retired identity evidence: transfers,
ordinary claims and mints stay disabled, while metadata/events clearly identify
the one successor. Cached third-party displays may still be stale. The successor
NFT requests the same 5% to its own correctly bound royalty ledger.

Future source royalty and creator-receipt modules need a **permanent fixed-
successor late-funding mode** before initial sealing. They accept plain transfers
where the old interface already accepts them, quarantine protected/unsupported
amounts, and allow permissionless exact typed forwarding of only authenticated
post-cutoff amounts to the committed successor. No source ownership claim or new
legacy reward index is activated. The candidate supplies direct same-chain late
forwarding; cross-chain envelopes, transport and finalized receipts remain open.

Distinguish unsplit new gross revenue from already allocated old liabilities in
separate envelopes. Never apply 80/10/5/5 twice. Pre-cutoff synchronized receipts
belong to the exported ledger. Truly later gross receipts follow the approved
receipt/processing-time policy when funded into the active canonical ledger;
an alternative historical-membership policy would require an explicit decision.
Late designated compounding and buyback obligations remain tagged to their
bucket/purpose and cannot become administrator spending.

Each legacy source forwards only to its one immediate successor with a monotonic
receipt nonce. If that successor later retires, its compatible late-funding mode
forwards onward without reallocating twice; strictly increasing epochs prevent
cycles. Actual historical-asset routes, backing and finality remain required. If
the old chain later halts permanently, old cached-address payments cannot be
guaranteed recoverable. Deferred post-halt recovery is not silently solved by this
forwarding design.

## Review requirements before any implementation is called ready

Acceptance must cover source/destination reorg and forged-readiness proofs; full
and partial funding; token insolvency, callbacks and forced prefunds; duplicate
NFT/asset records; fractional/index dust conservation; lazy-import denominator
attacks; old-owner versus buyer claims; contract-owner incompatibility; stale
approvals; VRF drain and exact remaining inventory; in-flight reward/ACK replay;
late royalty/creator receipts and multi-successor forwarding; abort at every
stage; and the impossibility of reopening terminal source claims.

Run whole-collection solvency invariants and bounded worst-case gas, an actual
source/destination rehearsal with the selected proof/bridge services, independent
review and remediation. These are design acceptance requirements, not completed
tests or a second task-status list. Authority/quorum, admissible successor code,
finality rules, notice/freeze deadlines, supported asset routes, data availability,
contract-owner handling and operating budgets remain unresolved release decisions.
