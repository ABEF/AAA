# Configuration changes and LP recovery boundaries

The LP is nonredeemable by NFT holders. This must not be confused with an LP
position that can never move: the migration framework can close the shared
position and move its accounted principal through a separately approved route.
No administrator can sweep that principal to a wallet.

The undeployed candidate uses fixed custody code and timelocked configuration.
It is not a general proxy upgrade system. Sealing fixes module addresses; the
following explicit configuration paths remain available after sealing.

| Change | Control and retained protection |
| --- | --- |
| Add, disable or re-enable an activation currency | The registry's immutable `ZZZActivationAssets` helper appends a policy through governance. Enabling requires reviewed code, matching decimals and a valid price. Disabling does not query the broken token or oracle. Existing claims, LP accounting and exit permission do not depend on this admission flag. |
| Reconfigure a pool after disabling a currency | Initial pool admission never overwrites a known asset policy. Reconfiguration cannot silently re-enable it. A zero amount on a disabled side does not block contribution of the enabled side. |
| Accept an asset outside the LP pair | The Registry's immutable [Entry child](ACTIVATION_ENTRY.md) implements owner-authenticated source custody, exact native wrapping or an admitted typed single-hop V3 conversion, and one original-source 99% deployed-LP floor. Governance appends pinned route policies; asset admission alone does not enable a route. Actual USDC routing and production route/feed/authority qualification remain open. |
| Replace a retired token-price feed | Existing governed `ZZZOracle.setFeed` configuration; the replacement must retain valid decimals, freshness and price checks. No caller-supplied price or automatic spot-price fallback. |
| Replace a failed sequencer-status feed | `ZZZOracle.setSequencerFeed` appends a reviewed nonzero source/code policy through the timelock without querying the failed old source. Uptime and recovery grace remain mandatory; a configured safeguard cannot be removed by setting zero. |
| Maintain the canonical native wrapper | Append and activate a reviewed wrapper policy through the timelock, checking the real proxy administrator, implementation, owner and code hashes. A reviewed renounced zero-owner state is allowed. The wrapper address and PoolKey stay fixed. |
| Disable new strategy operations in a pool | Mint, increase and swaps stop; typed collect/close remain available under custody, wrapper and real-key checks. Ordinary Vault exit validation ignores the source operations flag but still requires a valid oracle and acceptable spot deviation. Separately reviewed paused parking has raw-token authorization instead of a source USD read. |
| Move LP to another supported local pool | Governed `ZZZMigration.movePool` closes and redeploys the whole bucket through the Vault. Both pools must have the same ordered accounting currencies; the destination must be admitted and enabled. NFT shares and historical liabilities remain attached to the bucket. |
| Park a paused shared LP during a source-price outage | Sealed, paused `ZZZMigration.park` requires the exact timelocked LP/share/deposit/location/epoch/nonce snapshot, ordered currencies, reviewed close-only raw minima and a current deadline. It collects venue fees separately, closes the LP and keeps all principal attributed inside Vault. Old idle, donations and compound reserves cannot satisfy the close minimums. USD/sequencer reads and creator-inbox synchronization are omitted; native-wrapper and venue pins remain mandatory. |
| Resume or migrate parked principal | After unpause, governed `resume` requires valid valuation and normal enabled-destination, ordered-currency, swap/slippage, liquidity and idle guards. A proposed parked migration retains approved transport, delay, snapshot, exact-transfer and historical remote-liability funding barriers; already closed source principal needs no recovered source USD feed. Destination services and real bridge backing remain independent requirements. |
| Add a future chain, equivalent-asset pool or bridge provider | Register new immutable transport policies and routes, deploy and independently review the destination system, then approve the economic migration. Disabling outbound policies does not cancel historical inbound settlement. Actual bridge wrappers are not supplied by this framework. |
| Change keepers, guardians or strategy settings | Existing governed configuration and fixed timelock; guardian pause is not asset-withdrawal or upgrade authority. |
| Change the Vault, reward ledgers or mint/trait rules after sealing | No generic implementation replacement exists. A new code version needs an explicit reviewed migration design; these configuration controls do not make arbitrary code changes safe or possible. |

## Destination capacity: unresolved, proposed next implementation

The current `reservePool` binds a pool identity but does not reserve a historical
bucket slot. The [capacity regression](../test/ReservationCapacity.t.sol) reserves
a destination, fills its four slots with other first imports, then shows that the
original import reverts without accepting funds or changing incumbent custody.
Atomic rejection protects accounting; it does not complete an in-flight delivery.
Keep real bridging disabled until this admission gap is resolved and reviewed.

The proposed implementation is a **permanent reservation of a bucket slot**.
Reusing the bounded historical array with idempotent registration may avoid a
new ledger: reserve first, then activate/import into that same slot. This is a
design proposal, not implemented behavior. It must preserve these invariants:

- Reserved plus previously registered distinct bucket identities never exceed four.
- Repeating a reservation, reserving another pool for the same bucket, and
  returning/revisiting an existing bucket consume no extra slot. Another bucket
  cannot take a reserved pool or capacity slot.
- Local entry and remote first arrivals share the same admission accounting.
- A source cancellation, deadline or outbound route disable never releases the
  destination slot: an old packet, retry or historical return may still need it.
  Unused governance reservations therefore permanently consume capacity.
- Reserved buckets in `None` state are handled explicitly by enumeration,
  membership settlement, keeper discovery and read/indexer services.

Required regressions include reserve-first concurrent arrivals, rejection of the
fifth distinct reservation before departure, duplicates at capacity, local versus
remote admission, full-cap returns, failed-import rollback with commitment retained,
and source cancellation with retained capacity. Prove unchanged runtime/initcode
and gas limits: the current Vault has only 520 runtime bytes of headroom.

A newly deployed, independently reviewed destination can implement this while the
initial source stays sealed, preserving the v3 message and accounting interfaces.
The source's timelocked route registry already admits future remote Vault addresses.
However, the source does not verify a remote capacity proof: final destination
reservation must be verified during route admission and before departure. Returning
to the original source reuses its existing slot. This cannot patch a sealed
destination or enable same-chain replacement of a Vault.

## Edge cases that remain release considerations

- **External custody failure:** a stopped chain, frozen asset, hostile wrapper
  upgrade, failed venue or unavailable bridge may prevent recovery. No contract
  can guarantee movement of assets controlled by a failed external system.
- **Oracle outage:** ordinary upkeep and active-LP migration retain valuation
  checks. Governed token/sequencer feed replacement remains available. The
  [paused custody-parking path](CUSTODY_PARKING.md) now permits an exact,
  timelocked close into Vault-held currencies without source USD or sequencer
  reads. Governance must review raw per-asset close minimums and a fresh custody
  snapshot; this cannot bypass a failed venue, frozen token or incompatible
  native wrapper. Resume requires recovered valuation. Migration of already
  parked principal retains route, backing and funded-liability protections.
- **In-flight migration:** do not erase old routes, reinterpret existing
  messages, substitute unbacked tokens or release liabilities on a timeout alone.
  Real providers need reviewed retry, finality and funded recovery procedures.
- **VRF failure:** the current collection has immutable coordinator configuration
  and ordered reveal. A missing earlier fulfillment can block later reveals and
  activation. Provider liveness, recovery and any required replacement design
  remain explicit launch gates; adding an administrator reroll would compromise
  the accepted randomness rules.
- **Token changes:** a runtime pin alone cannot identify all proxy upgrades,
  freezes, rebases or transfer taxes. Admission needs dependency/authority review,
  and exact-transfer execution guards remain mandatory.

See the [release checklist](RELEASE_CHECKLIST.md) for outstanding qualification.
The [activation routing research](ACTIVATION_ROUTING.md) remains a historical
read-only venue/provenance snapshot, distinct from the implemented Entry and its
still-open production route qualification. [Custody parking](CUSTODY_PARKING.md)
documents exact authorization, close accounting, guarded resumption and retained
claim rights. Focused mocks and real-timelock tests, actual pool forks, testnet
operating rehearsals and independent audit are separate evidence layers.
These are development capabilities and limitations, not a deployment approval
or a guarantee that principal can be recovered in every failure scenario.
