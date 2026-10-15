# Paused custody parking

Parking closes a shared LP into its underlying accounting currencies and retains
those assets inside the immutable Vault. It is a governed recovery operation when
normal oracle-dependent upkeep cannot run. It creates no holder or administrator
withdrawal, redemption or arbitrary execution permission.

`PositionStatus.Parked` is appended as enum value **6**. Existing status values do
not change. The bucket, NFT shares, home identity, membership and reward rights
remain attached; the physical LP token ID becomes zero and principal is attributed
to that bucket's Vault idle ledger. No new LP fees are earned from a closed LP.

## Authority and exact authorization

The system must be sealed and paused. A guardian can pause quickly, but cannot
close an LP or receive its assets. After sealing, the existing controller timelock
must execute the exact `ZZZMigration.park(ParkingRequest)` call. The focused
governance test uses a two-day controller delay; actual operating delay is the
controller's immutable configured delay. Parking adds no instant emergency-admin
withdrawal mechanism.

The request binds:

- Bucket and pool identities, the exact LP token ID and local Vault location.
- Current total shares, recorded contribution value, custody epoch and parking nonce.
- Exact ordered accounting currencies and minimum close proceeds in raw token units.
- A deadline and nonzero review reference identifying the reviewed close evidence.

At least one currency minimum must be nonzero, allowing a genuine one-sided LP.
The runtime deadline must be current and no more than ten minutes ahead. When
scheduling through the timelock, choose a narrow execution window after the
operation becomes ready; an expired request cannot execute. The review hash is
provenance supplied by governance, not automatic proof of an independent audit.

A pending migration plan prevents parking. A rebalanced LP, changed share supply,
custody epoch, contribution record, ordered currencies, nonce or local location
invalidates an old snapshot. The parking nonce is consumed before external calls,
and failure rolls back the nonce, all custody changes and fee accounting.

Governance can call `invalidateParking(bucket)` to advance the nonce and invalidate
older request data. After sealing, that call follows the same timelock. Pending
timelock operations may also be cancelled through the controller's authorized
canceller role. Cancellation does not produce an alternative execution or payout
path. A successfully executed request cannot be replayed.

## Price-independent close, exact proceeds

Parking omits USD price and sequencer-feed reads. It also omits creator-inbox
synchronization, so an unrelated broken reward inbox does not prevent this custody
close. The selected Registry/venue/wrapper bindings are still validated.

Vault first collects existing venue fees and allocates them through the normal
fee ledger. It then closes the LP and records the actual increase in each token's
attributed idle balance. Migration checks those close deltas against the reviewed
raw minima. Old idle balances, direct Vault donations and compound reserves held
in the fee controller cannot satisfy those minima. Collected venue fees remain
allocated rewards/reserves rather than becoming principal close proceeds.

The liquidity manager retains its typed position checks and venue-level close
minima derived from current position amounts and configured slippage. Parking is
independent of an external USD feed; it does not bypass position ownership, pool
identity, venue settlement, exact token transfers or native-wrapper conservation.
Any failure reverts the complete operation and leaves the original LP state.

## Resume or migrate

While parked, ordinary activation into that bucket, additions, compounding and
keeper rebalancing remain disabled. Existing principal stays nonredeemable.
Governance has two paths after the system is unpaused:

| Path | Required protections |
| --- | --- |
| `Migration.resume` | No pending migration plan; reviewed enabled destination pool with the same ordered currencies; recovered valid valuation; normal swap/slippage, minimum-liquidity and idle checks. The original pool may be reused. |
| Proposed migration of a parked bucket | Approved route/transport and frozen custody snapshot; normal proposal/execution delay; funded historical remote liabilities; exact token provenance, custody transfers, nonce/epoch and receipt checks. No old source LP exists to close, so source USD recovery is unnecessary. |

Resume brings designated compound reserves into the bucket and redeploys the
principal under current oracle and strategy guards. It cannot bypass a stale or
broken feed. A failed resume leaves the bucket parked with the same shares and
assets. This does not authorize changing the accounting pair through an arbitrary
swap or moving assets to an administrator wallet.

For a parked cross-chain migration, `releaseForMigration` retains the
`remoteSettled` funding barrier, includes designated compound reserves and sends
only the bucket's attributed currencies to the fixed migration module. A stale
source USD feed therefore need not trap already parked principal, while missing
historical remote reward backing still blocks departure. Destination deployment,
price validation, bridge backing/finality and receipt authentication remain
independent requirements. A timeout alone is not proof that a bridge transfer was
cancelled, and cannot authorize duplicate principal release.

## NFT and reward behavior

Parking preserves NFT ownership, immutable traits, LP shares, royalty weights and
collective membership. Funded LP rewards and admitted royalties remain claimable
by the current holder, including through the bounded claim router. A transfer
continues to carry the attached shares and unclaimed/future rights. Existing or
newly admitted creator funding can be processed under the parked reward policy;
parking itself does not fabricate continued LP revenue.

Current marked LP valuation is explicitly unavailable while parked. Metadata uses
the labelled Activated artwork fallback, rather than showing a made-up USD value
or revoking activation and royalty eligibility.

## Limits and release evidence

Parking cannot force a failed or malicious PoolManager, position manager, token,
native wrapper or chain to return assets. Reviewed wrapper/feed policy replacement
can restore compatible dependencies, but incompatible immutable venue failure,
issuer blacklisting, token confiscation and bridge insolvency remain real risks.
There is no universal recovery guarantee or hidden rescue wallet.

Focused custody, timelock, parked-reward and native-pool tests are recorded
separately from the final full regression and current-source static review.
Actual operating requests need freshly reviewed raw minima and snapshots,
authority review, staging, realistic gas/strategy qualification and independent
audit/remediation. This document authorizes neither deployment nor transactions.
