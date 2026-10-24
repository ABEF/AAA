**Current policy, 2026-10-24:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Defaults are 1% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.

# Governed custody handoff

Undeployed candidate. Replaces the old v3 LP bridge stack and typed pair executor;
the separate whole-collection ownership/reward handoff is retained. See the
[native ETH candidate verification](../reports/native-eth-port/VERIFICATION.md).
Earlier [custody evidence](../reports/custody-handoff/VERIFICATION.md) retains its original WETH-accounting scope.

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
| Bucket principal | Pause and use reviewed `Migration.park(ParkingRequest)` before approving the stable parked snapshot, then `exit(id)`. Only the bucket's attributed principal leaves. |
| Holder LP rewards, pending compound, buyback reserves | Stay in their existing ledgers; not swept or subsidizing principal conversion. Consolidate pending compound separately through supported upkeep before planning if desired. |
| Marketplace royalties | Per-currency `RoyaltyRewards.exitCustody(...)`; original NFT liabilities and quarantine remain. Full same-currency restoration is required by `returnCustody(...)`. |
| Whole collection | Existing canonical handoff carries NFT ownership, shares and both complete ledgers to one reviewed same-chain successor. It cannot freeze while external custody is outstanding. |

## Move funds without external custody

Use `Migration.moveFunds(bucket,destinationPool,minimumLiquidity,deadline)` for a
new fee tier with the **same actual ordered currencies**, such as another native
ETH/ZZZ pool. The older `movePool` selector is an alias with the same authority/guards. It never sends principal to your wallet.

1. Governance reviews and admits the initialized, hookless destination with
   `PoolRegistry.configureNative` (static native ETH/ZZZ on the pinned Robinhood
   core) or ordinary `configure` (WETH/ZZZ). Set destination deposits disabled;
   operations must be enabled. Verify real key, fees, spacing, reference
   price, depth and destination reservation conflicts. A wrapper review applies only
   when an actual WETH operation is being proposed. No new core deployment is
   needed for these supported venue changes after sealing.
2. Stop new source deposits and review a fresh confirmed snapshot. Preserve source
   operations if balancing needs them. Simulate the complete move with an actual
   positive minimum liquidity and deadline at most ten minutes away. Execute via
   controller governance while unpaused. No new holder approval is required.
3. The atomic operation harvests old fees, includes designated compound, closes
   source LP, balances and creates destination LP owned by Vault. It retains at
   least 97% of starting principal plus released compound, at one starting price
   vector. This 3% overall cap is fixed after sealing; gas is separate. Any failed
   settlement or limit rolls back the whole move, including closing the old LP.
4. Verify actual destination LP, pool ID, unchanged NFT shares/home identity,
   existing reward liabilities and cleared allowances. Governance then enables
   this sole contribution pool and separately updates reviewed input routes/API/
   keeper configuration. Do not reactivate the old physical pool for new entries.

Native ETH is `address(0)`; WETH is a distinct ERC20. **An atomic ETH/WETH pool
move is not implemented and fails the same-pair guard.** It needs an explicit,
reviewed conversion/accounting boundary before it can be supported; admitting a
new pool does not supply that algorithm. Other different tokens, reversed pairs,
another bucket's reservation, unsupported hooks and dynamic native pools also
fail closed. Use the separately approved external custody procedure below for
manual token exchange, bridging or a return to a reviewed different pair.

## Ordinary Migration Exit: all principal into ZZZ

1. Independently qualify the selected ZZZ contract, source/destination venue,
   input/output units, prices, recipient and any destination verifier. Governance
   calls `Migration.configureZZZ(token,expectedCodeHash,reviewHash)` with an admitted
   Rewards asset and healthy USD feed. No outstanding principal plan may exist.
   A future replacement ZZZ can be configured after sealing. Review its burn
   interface and update `Buyback.setZZZ(...)` separately; neither setter moves funds.
   Before parking, record the reviewed principal-plus-idle USD value and the
   configured ZZZ price/decimals at the same block. Compute the original raw ZZZ
   minimum by rounding **up** the quantity needed to retain at least 97% of that
   value at those prices. Preserve this amount through the later approval.
2. For a planned local destination, governance first calls
   `Vault.reservePool(destinationPool,bucket)` and verifies its permanent alias
   belongs to that bucket. This prevents a competing activation from consuming
   the destination while custody is outside.
3. Pause globally. If an unsent custody plan already exists, governance must
   cancel it before parking: `activePlan(bucket)` must be zero. Review and execute
   `Migration.park(ParkingRequest)` with the current pool, LP token ID, total
   shares, recorded `depositUSD`, custody epoch, parking nonce, ordered accounting
   currencies, raw close minima, deadline and nonzero review hash. At least one
   close minimum must be positive. The deadline must be current and at most ten
   minutes away. Verify `ParkingExecuted`, `PositionStatus.Parked`, zero LP token
   ID and actual attributed idle amounts. Existing idle, donations and separately
   collected fees cannot satisfy the parking close minima. See
   [the exact parking checks](CUSTODY_PARKING.md#authority-and-exact-authorization).
4. Read `Migration.sourceSnapshot(bucket)` and the complete parked `Vault.group`
   at a fresh confirmed block, including total NFT shares and exact idle amounts.
   Build `Request` binding that snapshot, recipient/code hash, destination chain,
   custody, pool, ordered output tokens, exact raw output minima, `minimumZZZ`,
   deadline (at most ten minutes), and review hash. Set `rawExit=false`.
   The source pair must contain the configured ZZZ. Output asset identities are
   the Registry's actual accounting currencies: native ETH is `address(0)`,
   not the WETH token address.
   Set `minimumZZZ` to the **greater** of the preserved pre-parking raw minimum
   and the rounded-up minimum required by the parked approval's current value
   and ZZZ price. Never lower the pre-parking minimum to make an exit execute.
5. Simulate approval and the **complete exit**, including the actual available
   source-pool swap after withdrawing PoPL liquidity. Governance approves the
   request. No principal leaves at approval. Keep the system paused and call
   `exit(id)` before its deadline. The exit swaps the entire other attributed
   principal side into ZZZ, clears temporary approvals and sends exactly the
   resulting ZZZ to the approved recipient. It does not close an already parked
   LP again. Failed swap, minimum, transfer or snapshot checks revert the exit;
   they do not undo the earlier, separately confirmed parking transaction.
   The contract enforces at least 97% of the parked principal value at approval,
   rounding against excess loss; gas is separate. Parking has its own raw close
   minima and venue guards. The preserved, no-loosening `minimumZZZ` above is
   required to retain the reviewed 3% budget across parking and conversion.
   The contract does not autonomously combine separate parking and approval
   transactions into one pre-parking cached price-vector budget.
6. Verify `CustodyAssetsSent`, actual recipient transfers, source `Outbound`
   status, zero source LP/idle, unchanged NFT ownership/shares and reward ledgers.
   Record the actual sent amount, not merely the minimum. Never resend a
   successful exit. Source LP valuation is unavailable, not zero. Growth and
   upkeep cannot run on this outbound bucket; existing funded claims/transfers
   and original creator inboxes retain their existing rights.

**Why park before the snapshot?** An active source snapshot commits the LP's live
token quantities. External Uniswap swaps can change those quantities even while
PoPL is globally paused. A separately mined active approval and exit can therefore
become incompatible. Parking first removes this moving quantity from the snapshot
without weakening its exactness. If using the supported direct active exit instead,
review approval and exit as one controller batch; it still fails closed if the
reviewed snapshot changed before inclusion, and its original 3% budget includes
the in-transaction close and conversion. Never bypass a stale snapshot check.

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
Use the same pause, reviewed parking and stable-snapshot sequence above. Cancel
an existing unsent plan before parking or replacing its approval. For an already
parked source, `exitMinimum0/exitMinimum1` bound the total attributed currencies
sent, including existing idle; the preceding parking request separately bounds
the actual LP close proceeds. A direct active exit closes and sends in one
transaction, subject to the active-snapshot limitation above. No conversion or
source USD read is required, and at least one raw exit minimum must be positive.
The ordinary request never falls back to this mode automatically.

This is an explicit acceptance of raw-token custody and valuation risk: **the
ordinary 3% USD execution guarantee does not apply**. The close minima, exact
transfers, shares, recipient and asset segregation remain enforced. A failed
venue or nontransferable/frozen token can still prevent exit. Donations, other
buckets, rewards, royalty assets and fee reserves are not included.

### Native ETH versus WETH at exit

The native-accounting V2 candidate sends **native ETH and ZZZ** for a raw exit
from this pool. Normal exit still consolidates principal into ZZZ. Native pool
settlement, fee classification, parking, raw exit and full native recovery do not
call WETH or its policy. An optional broken wrapper therefore does not block
these native paths.

This is not universal recovery: core/token runtime bindings, usable settlement,
transferable ZZZ and a recipient that accepts ETH are still required. A failed
close, recipient callback or transfer reverts that transaction; an approved raw
mode never bypasses exact minima or sweeps earned rewards. The unconfigured
`currentZZZ == address(0)` sentinel must not relabel native ETH as ZZZ.
See [native design and remaining qualification](NATIVE_ETH_ARCHITECTURE.md).

## Local completion, recovery and stopping

`completeLocal(id,amount0,amount1,minimumLiquidity,deadline)` can be funded by the
recipient or another caller. ERC20 currencies require exact approvals; for a
native output currency, attach exactly its declared amount as `msg.value`.
ERC20-only completion requires zero ETH. Existing prefunds are not return funding.
The operation actually mints LP in the admitted destination and checks backing before closing
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
back, in a single funded transaction. Attach exactly the actually sent native
amount as `msg.value` and approve only the required ERC20 amounts. Extra or missing
ETH, failed funding or rejected settlement reverts the complete return; old native
prefunds cannot fill a shortfall. It restores parked principal, not an
accounting-only receipt or an automatically reopened LP. It can run while paused;
fresh reviewed `resume(...)` is required later. A sent request cannot be cancelled
or erased after a timeout. An approved, unsent request can be cancelled through
governance, including while draining preparation. Every record/nonce remains
historical; replay and conflicting per-bucket plans are rejected.

## New-chain boundaries

The recipient is always an address **on the source chain**. It may subsequently
bridge; sending assets to a numeric address does not itself cross chains.
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
Use fresh native-accounting version 2 API/keeper profiles with exact reviewed
runtime pins and `Vault.ACCOUNTING_VERSION() == 2`. Version 1 WETH journals and
predecessor history must not be reinterpreted or reset. The existing 8902 fixture
and its saved transactions remain unchanged; the public website deployment is
null and website V2 integration still requires qualification.

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
