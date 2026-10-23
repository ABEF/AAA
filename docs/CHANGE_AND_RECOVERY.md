# Configuration changes and LP recovery boundaries

The LP is nonredeemable by NFT holders. This must not be confused with an LP
position that can never move: the migration framework can close the shared
position and move its accounted principal through a separately approved route.
There is no direct local administrator sweep. Approved external providers and
remote custody remain trust boundaries; exact source depletion does not prove
honest delivery.

The undeployed candidate uses fixed custody code and immediate governance-approved configuration.
It is not a general proxy upgrade system. Sealing fixes module addresses; the
following explicit configuration paths remain available after sealing.

| Change | Control and retained protection |
| --- | --- |
| Add, disable or re-enable an activation currency | The registry's immutable `ZZZActivationAssets` helper appends a policy through governance. Enabling requires reviewed code, matching decimals and a valid price. Disabling does not query the broken token or oracle. Existing claims, LP accounting and exit permission do not depend on this admission flag. |
| Disable a pool during dependency failure | Governed `PoolRegistry.disablePool(poolId,stopDeposits,stopOperations)` only clears selected flags of an admitted pool, without token/oracle/venue calls. Re-enabling still requires full configure/configureNative checks. Global pause permits configuration; preparation/canonical locks do not. |
| Pause only new NFT mints | Governed `NFT.setMintPaused(bool)` blocks new requests/mints without pausing pending reveals or existing LP/claim/transfer paths. Clearing it does not override other controls. This operational setting must be reviewed independently on a replacement. |
| Reconfigure a pool after disabling a currency | Initial pool admission never overwrites a known asset policy. Reconfiguration cannot silently re-enable it. A zero amount on a disabled side does not block contribution of the enabled side. |
| Accept an asset outside the LP pair | The Registry's immutable [Entry child](ACTIVATION_ENTRY.md) implements owner-authenticated source custody, exact native wrapping or an admitted typed single-hop V3 conversion, and one original-source 99% deployed-LP floor. Governance appends pinned route policies; asset admission alone does not enable a route. Actual USDC routing and production route/feed/authority qualification remain open. |
| Replace a retired token-price feed | Existing governed `ZZZOracle.setFeed` configuration; the replacement must retain valid decimals, freshness and price checks. No caller-supplied price or automatic spot-price fallback. |
| Replace a failed sequencer-status feed | `ZZZOracle.setSequencerFeed` appends a reviewed nonzero source/code policy through the governance controller without querying the failed old source. Uptime and recovery grace remain mandatory; a configured safeguard cannot be removed by setting zero. |
| Maintain the canonical native wrapper | Append and activate a reviewed wrapper policy through the governance controller, checking the real proxy administrator, implementation, owner and code hashes. A reviewed renounced zero-owner state is allowed. The wrapper address and PoolKey stay fixed. |
| Disable new strategy operations in a pool | New LP mint, increase and guarded swaps stop; typed collect/close remain available under custody, wrapper and real-key checks. Ordinary Vault exit validation ignores the source operations flag but still requires a valid oracle and acceptable spot deviation. Separately reviewed paused parking has raw-token authorization instead of a source USD read. |
| Move LP to another supported local pool | Governed `ZZZMigration.movePool` closes and redeploys the whole bucket through the Vault. Both pools must have the same ordered accounting currencies; the destination must be admitted and enabled. NFT shares and historical liabilities remain attached to the bucket. |
| Convert principal into another local pair | The constructor-created `Migration.pairMigration()` executes an exact governed request with at most eight typed v4 swap legs and fixed Vault custody. Close, designated compound conversion and deployment share one fixed-price 3% limit, gas separate. Original reward currencies/inboxes persist; late historical compound remains incumbent backing. See [procedure and limits](PAIR_MIGRATION.md). V3 principal bridging is blocked after composition; future-chain multi-currency accounting is still pre-seal work. |
| Park a paused shared LP during a source-price outage | Sealed, paused `ZZZMigration.park` requires the exact governance-approved LP/share/deposit/location/epoch/nonce snapshot, ordered currencies, reviewed close-only raw minima and a current deadline. It collects venue fees separately, closes the LP and keeps all principal attributed inside Vault. Old idle, donations and compound reserves cannot satisfy the close minimums. USD/sequencer reads and creator-inbox synchronization are omitted; native-wrapper and venue pins remain mandatory. |
| Resume or migrate parked principal | After unpause, governed `resume` requires valid valuation and normal enabled-destination, ordered-currency, swap/slippage, liquidity and idle guards. A proposed parked migration retains approved transport, snapshot, exact-transfer and historical remote-liability funding barriers; already closed source principal needs no recovered source USD feed. Destination services and real bridge backing remain independent requirements. |
| Add a future chain, equivalent-asset pool or bridge provider | Register new immutable transport policies and routes, deploy and independently review the destination system, then approve the economic migration. Disabling outbound policies does not cancel historical inbound settlement. Actual bridge wrappers are not supplied by this framework. |
| Change keepers, guardians or strategy settings | Existing governed configuration and zero-delay controller; guardian pause is not asset-withdrawal or upgrade authority. |
| Change the Vault, reward ledgers or mint/trait rules after sealing | No generic implementation replacement exists. A new code version needs an explicit reviewed migration design; these configuration controls do not make arbitrary code changes safe or possible. |

<a id="destination-capacity-unresolved-proposed-next-implementation"></a>
## Destination capacity: permanent admission

`reservePool` now registers a distinct bucket in the same permanent bounded set
used for historical custody. At most four identities are admitted, including
unfunded reservations. Duplicate reservations, pool aliases and returns reuse
their slot even at capacity. Reassignment and a fifth identity reject before
arrival. Cancellation, timeout, departure and disabled operations never free a
slot that an old packet may still need.

Reserved buckets remain in `None` state with no shares or attributed principal.
Membership and keeper discovery skip them before pool/price reads. The
[capacity and switching regressions](../reports/architecture-evolution/VERIFICATION.md)
cover admission, arrival, rollback, aliases, full-cap returns, identity/reward
preservation and combined gas. An unfunded reservation is not TVL or an NFT.

This repairs the earlier identity-only reservation defect. It does not prove an
external provider delivers funds or authenticate destination capacity on the
source chain. Governance must verify the exact destination implementation and
confirmed admission before departure; arbitrary reservations can permanently
exhaust the four slots. Real bridging remains disabled pending independent
admission, provider/backing and operating qualification.

A reviewed new remote destination can implement the repair while a source stays
sealed. It cannot patch an already sealed old destination, rebind the canonical
NFT/Rewards contracts or enable same-chain replacement of a Vault. Different-pair
conversion and the proposed aggregate **3% migration execution budget** require
the [composition-epoch architecture](ARCHITECTURE_EVOLUTION.md); they are not
implemented by this capacity repair. Activation/top-ups retain **1%**.

## Edge cases that remain release considerations

- **External custody failure:** a stopped chain, frozen asset, hostile wrapper
  upgrade, failed venue or unavailable bridge may prevent recovery. No contract
  can guarantee movement of assets controlled by a failed external system.
- **Oracle outage:** ordinary upkeep and active-LP migration retain valuation
  checks. Governed token/sequencer feed replacement remains available. The
  [paused custody-parking path](CUSTODY_PARKING.md) now permits an exact,
  governance-approved close into Vault-held currencies without source USD or sequencer
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

See the [central Todo](../TODO.md) for outstanding qualification and the [release record](RELEASE_CHECKLIST.md) for final approval.
The [activation routing research](ACTIVATION_ROUTING.md) remains a historical
read-only venue/provenance snapshot, distinct from the implemented Entry and its
still-open production route qualification. [Custody parking](CUSTODY_PARKING.md)
documents exact authorization, close accounting, guarded resumption and retained
claim rights. Focused mocks and real-controller tests, actual pool forks, testnet
operating rehearsals and independent audit are separate evidence layers.
These are development capabilities and limitations, not a deployment approval
or a guarantee that principal can be recovered in every failure scenario.
