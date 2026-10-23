# Governed custody handoff

Undeployed candidate. Replaces the old v3 LP bridge stack and typed pair executor;
the separate whole-collection ownership/reward handoff is retained. See the
[current verification record](../reports/custody-handoff/VERIFICATION.md).

## Authority and custody guarantee

The sealed `ZZZMigration` implementation authorizes exact principal handoffs to
future recipients chosen by immediate governance. A recipient can be an EOA or
contract. Governance explicitly trusts its custody, execution and liveness:
**once sent, that recipient can lose or divert the assets**. Source accounting
cannot compel an external wallet to return them. Normal loss checks do not remove
this trust. There is no holder redemption, general Vault sweep or arbitrary-call
facility. New recipient addresses do not require unsealing/rebinding the core.

These are separate custody domains:

| Domain | Exit and completion |
| --- | --- |
| Bucket principal | `Migration.approve(Request)` then paused `exit(id)`. Only the bucket's current LP and attributed Vault idle leave. |
| Holder LP rewards, pending compound, buyback reserves | Stay in their existing ledgers; not swept or subsidizing principal conversion. Consolidate pending compound separately through supported upkeep before planning if desired. |
| Marketplace royalties | Per-currency `RoyaltyRewards.exitCustody(...)`; original NFT liabilities and quarantine remain. Full same-currency restoration is required by `returnCustody(...)`. |
| Whole collection | Existing canonical handoff carries NFT ownership, shares and both complete ledgers to one reviewed same-chain successor. It cannot freeze while external custody is outstanding. |

## Ordinary Migration Exit: all principal into ZZZ

1. Independently qualify the selected ZZZ contract, source/destination venue,
   input/output units, prices, recipient and any destination verifier. Governance
   calls `Migration.configureZZZ(token,expectedCodeHash,reviewHash)` with an admitted
   Rewards asset and healthy USD feed. No outstanding principal plan may exist.
   A future replacement ZZZ can be configured after sealing. Review its burn
   interface and update `Buyback.setZZZ(...)` separately; neither setter moves funds.
2. For a planned local destination, governance first calls `Vault.reservePool(destinationPool,bucket)` and verifies its permanent alias belongs to that bucket. This prevents a competing activation from consuming the destination while custody is outside. Read `Migration.sourceSnapshot(bucket)` at the confirmed reviewed block, the
   complete `Vault.group`, total NFT shares and exact venue/idle quantities.
   Build `Request` binding that snapshot, recipient/code hash, destination chain,
   custody, pool, ordered output tokens, exact raw output minima, `minimumZZZ`,
   deadline (at most ten minutes), and review hash. Set `rawExit=false`.
   The source pair must contain the configured ZZZ. Output asset identities are
   the Registry's accounting currencies, e.g. native ETH normalized as WETH.
3. Simulate approval and the **complete exit**, including the actual available
   source-pool swap after withdrawing PoPL liquidity. Governance approves the
   request. No principal moves at approval. Cancel stale approvals explicitly.
4. Pause globally, then governance calls `exit(id)` before its deadline. Within
   one transaction the Vault collects venue fees into their own ledgers, closes
   the LP, swaps the entire other principal side into ZZZ, clears temporary
   approvals and sends exactly the resulting ZZZ to the approved recipient.
   The explicit ZZZ minimum must retain at least 97% of starting LP plus idle at
   the review's fixed price vector, rounding against excess loss. Gas is separate.
   Failed close, swap, minimum, transfer or snapshot checks revert this entire exit.
5. Verify `CustodyAssetsSent`, actual recipient transfers, source `Outbound`
   status, zero source LP/idle, unchanged NFT ownership/shares and reward ledgers.
   Record the actual sent amount, not merely the minimum. Never resend a
   successful exit. Source LP valuation is unavailable, not zero. Growth and
   upkeep cannot run on this outbound bucket; existing funded claims/transfers
   and original creator inboxes retain their existing rights.

An issuer's 1:1 or 1:10 migration can be performed by the approved recipient
outside the source contracts. No standard issuer ABI is assumed. Approval must
bind the reviewed destination assets, raw units/decimals and minimum backing.
Token counts are not USD values and do not multiply NFT shares.

## Custody-only holding before a destination is selected

For either normal or raw exit, governance may approve local temporary holding
without selecting a new LP yet: `destinationPool=0`, `destinationChain=block.chainid`,
`destinationCustody=recipient`, and output identities equal the source pair.
Destination minima may be zero in this explicit holding mode; raw **close**
minima still apply and normal ZZZ/value minima still apply. This does not query
or require an enabled destination pool, so a stopped source and unavailable
prices cannot defeat the raw fallback merely because a replacement is not ready.
Holding does not establish completed LP or remote delivery. For a later local
return, governance first admits and reserves the destination pool for the same
bucket, then calls `bindLocalDestination(id,pool,minimum0,minimum1,reviewHash)`.
This binding is one-time and available only to a sent local holding plan. It
preserves the source snapshot, actual departure amounts, raw/normal mode and
original loss budget; it derives output currencies from the admitted pool.
`completeLocal` then requires actual destination-token funding and deployed LP.
This supports an issuer's token exchange without requiring burned old tokens
back, while preserving the normal original 97% floor or raw destination minima.

Alternatively, full original-asset `recover` remains available. External bridging
and issuer operations are the recipient's responsibility; local destination binding
cannot change chains, waive remote finality or authenticate those operations.

## Emergency Exit: send the assets without a swap

When no safe swap route exists, governance can instead approve a **separate**
request with `rawExit=true` and explicit `exitMinimum0/exitMinimum1` close minima.
It closes and sends both attributed pool currencies, without a conversion or
source USD read. At least one close minimum must be positive. The ordinary
request never falls back to this mode automatically.

This is an explicit acceptance of raw-token custody and valuation risk: **the
ordinary 3% USD execution guarantee does not apply**. The close minima, exact
transfers, shares, recipient and asset segregation remain enforced. A failed
venue or nontransferable/frozen token can still prevent exit. Donations, other
buckets, rewards, royalty assets and fee reserves are not included.

## Local completion, recovery and stopping

`completeLocal(id,amount0,amount1,minimumLiquidity,deadline)` can be funded by the
recipient or another caller. It pulls those exact approved output currencies,
actually mints LP in the admitted destination and checks backing before closing
the plan. It needs unpaused healthy local venue/price services, nonzero LP, the
normal idle guards and unchanged NFT shares. Normal mode rechecks the **same
original** 97% floor after deployment; closing, consolidation and redeployment
cannot each spend separate 3% budgets. Raw mode instead enforces the explicit
destination raw-token minima after deployment; it makes no USD-loss claim.
Failures revert the attempted funding and mint, leaving the original sent plan.

Governance deliberately switches the sole contribution pool and input routes
only after verifying completion. A custody move does not change these policies.
Keep old funding addresses and conversion paths for historical reward currencies.
Historical compound remains incumbent NAV, not a new contributor's LP.

`recover(id,deadline,proof)` requires **all actual sent currencies and quantities**
back, in a single funded transaction. It restores parked principal, not an
accounting-only receipt or an automatically reopened LP. It can run while paused;
fresh reviewed `resume(...)` is required later. A sent request cannot be cancelled
or erased after a timeout. An approved, unsent request can be cancelled through
governance, including while draining preparation. Every record/nonce remains
historical; replay and conflicting per-bucket plans are rejected.

## New-chain boundaries

The recipient is always an address **on the source chain**. It may subsequently
bridge; sending ERC20s to a numeric address does not itself cross chains.
Remote approval requires a pinned, reviewed `ICustodyFinality` verifier.
`verifyRemote(id,proof)` verifies the domain-separated `proofCommitment(id,1)`:
source deployment/plan, bucket/share snapshot, actual departure quantities,
destination chain/custody/pool/assets/minima, review and departure block are bound.
A remote recovery additionally verifies `proofCommitment(id,2)`, including final
cancellation/closure of remote claims and in-flight delivery. There is no
governance-only, empty-proof, timeout or changed-verifier override.

**No real finality verifier, bridge provider or new remote ledger is supplied by
this change.** A permissive fixture verifier is not production evidence. Proof
quality and recipient security still require independent review. A verified
remote plan stays outstanding and its source LP stays unavailable; this does
not invent remote NAV, fund rewards, relocate NFT ownership or enable the old
two-token v3 messages. Future-chain reward delivery, canonical ownership/ledger
handoff and repeated remote custody hops remain separate qualification work.

## Marketplace royalty currencies

The royalty receiver can use the separately governed, paused
`exitCustody(asset,recipient,expectedBalance,nonce,recipientCodeHash,reviewHash)`.
Read `assetCount/assets`, `custodyNonce`, raw balance, index, liabilities and
quarantined funds at one confirmed block first. An admitted token needs no swap
route or price feed to leave in its original units. Native ETH is asset zero.
The entire exact currency balance is synchronized to its existing eligible
cohort and transferred; its original per-NFT rights, fractions and quarantine
classification remain recorded. Other currencies and LP principal are separate.

A combined claim that includes an exited currency reverts atomically; select healthy currencies or LP-only claims instead. Claims, conversion, synchronization and current claimable valuation for that
currency fail explicitly while its custody is external. Healthy currencies can
continue. Optional-currency activation isolation still applies if operations
are reopened: no newcomer receives old royalties. NFT ownership transfers carry
the same recorded entitlement. Do not advertise these external funds as
currently claimable or treat them as new principal.

`returnCustody(asset,expectedId)` must actually restore the full original raw
amount, including exactly matching `msg.value` for ETH. A donation already in
the receiver is not a substitute for funding the return. Returning custody is
not new income; only additional receipts enter the normal royalty index later.
There is no timeout completion or administrator write-off. Whole-collection
capture is blocked until all these funds are back. A future remote royalty
ledger/converted-currency handoff needs a reviewed accounting design before it
can replace this raw-return path; simply paying the external address is not it.

Unadmitted unsolicited assets are not automatically holder royalties. Follow
existing admission/prefund quarantine rules; do not relabel them or bypass a
token that cannot report balances or transfer.

## Release and monitoring requirements

Inventory the one Migration runtime/controller, configured ZZZ/code hash,
outstanding plans, source/destination snapshots, verifier pins and every royalty
custody nonce/balance. The removed bridge/pair-helper inventory is historical;
production inventory/service adaptation must be reviewed for the new layout.
Alert on pending custody age, unauthorized state changes, token/recipient code
changes, proof failures and missing returns. A crash can resume from contract
records; no server-held nonce or timeout decides who owns backing.

Real pool exit depth, target routes/feeds, recipient controls, new-token/burn
compatibility, target-chain gas, finality providers, royalty operating rehearsals
and independent audit remain release gates. Track these in the
[single Todo](../TODO.md#task-custody-composition).

The immutable `validation()` companion checks request, destination and parking
admission through view calls. It has no asset custody or execution method. Its
constructor binds its parent; ordinary callers cannot invoke its validation paths.

Resolve external custody before whole-collection preparation. Principal return
and destination completion deliberately reject preparation; if a notice was
already announced, cancel that exact notice before restoring principal. Freeze
rejects unresolved custody and never forgives missing backing.
