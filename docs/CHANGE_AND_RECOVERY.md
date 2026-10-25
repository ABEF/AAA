# Configuration changes and LP recovery boundaries


## Current release simplification - 2026-10-25

[Current scope](SIMPLIFIED_RELEASE.md): ETH/ZZZ-only contributions, actual local LP
fees, no creator inboxes or integrated cross-chain bridge. Preserve same-chain
pool moves, external custody exit/recovery, royalty currencies and complete
collection handoff. Current fee/custody profiles and canonical schema are
explicit; old deployments/journals keep historical profiles.

**Current candidate (2026-10-24):** [governed custody handoff](GOVERNED_CUSTODY_HANDOFF.md) replaces the legacy LP v3 bridge/pair executor. Whole-collection handoff remains separate. Normal all-ZZZ exit, explicitly approved raw emergency exit and separate royalty-currency custody are local candidates; real finality/remote accounting, the updated production inventory and independent qualification remain open. Earlier descriptions/evidence retain their historical scope. [Native V2 verification](../reports/native-eth-port/VERIFICATION.md). Earlier [custody evidence](../reports/custody-handoff/VERIFICATION.md) retains its WETH-accounting source scope.

The LP is nonredeemable by NFT holders. Governance can atomically move it between supported same-actual-pair pools or release attributed principal to explicitly approved external custody. Recipient custody and liveness are accepted trust; the source cannot compel return. No generic executor or sweep exists. See [selection](POOL_SELECTION.md), [policy](POST_SEAL_POLICY.md) and [native V2 scope](NATIVE_ETH_ARCHITECTURE.md).

The undeployed candidate uses fixed custody code and immediate governance-approved configuration.

**Current policy, 2026-10-24:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Defaults are 1% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.


It is not a general proxy upgrade system. Sealing fixes module addresses; the
following explicit configuration paths remain available after sealing.

| Change | Control and retained protection |
| --- | --- |
| Add, disable or re-enable an activation currency | The registry's immutable `ZZZActivationAssets` helper appends a policy through governance. Enabling requires reviewed code, matching decimals and a valid price. Disabling does not query the broken token or oracle. Existing claims, LP accounting and exit permission do not depend on this admission flag. |
| Disable a pool during dependency failure | Governed `PoolRegistry.disablePool(poolId,stopDeposits,stopOperations)` only clears selected flags of an admitted pool, without token/oracle/venue calls. Re-enabling still requires full configure/configureNative checks. Global pause permits configuration; preparation/canonical locks do not. |
| Pause only new NFT mints | Governed `NFT.setMintPaused(bool)` blocks new requests/mints without pausing pending reveals or existing LP/claim/transfer paths. Clearing it does not override other controls. This operational setting must be reviewed independently on a replacement. |
| Reconfigure a pool after disabling a currency | Initial pool admission never overwrites a known asset policy. Reconfiguration cannot silently re-enable it. A zero amount on a disabled side does not block contribution of the enabled side. |
| Accept an asset outside the LP pair | The Registry's immutable [Entry child](ACTIVATION_ENTRY.md) implements owner-authenticated source custody, exact native ETH funding or an admitted typed single-hop v3/v4 conversion, and one original-source governed deployed-LP floor (99% by default). Governance appends pinned route policies; asset admission alone does not enable a route. Actual USDC routing and production route/feed/authority qualification remain open. |
| Replace a retired token-price feed | Post-seal immediate governance calls `ZZZOracle.setDualFeed(token,primary,secondary,maxDeviationBps,reviewHash)`. Both independently reviewed sources must pass runtime/precision/round/freshness/disagreement admission. A new immutable policy/history entry is activated; update approved inventory/API/keeper policies afterward. The retired `setFeed` reverts. No redeployment, caller-supplied price or automatic spot/single-source fallback. |
| Replace a failed sequencer-status feed | `ZZZOracle.setSequencerFeed` appends a reviewed nonzero source/code policy through the governance controller without querying the failed old source. Uptime and recovery grace remain mandatory; a configured safeguard cannot be removed by setting zero. |
| Record an optional/legacy WETH wrapper review | The retained Registry policy API appends/activates a reviewed policy for the fixed WETH address, checking administrator, implementation, owner and runtime hashes. This is not native ETH admission or recovery authority: native V2 does not consult this policy. An explicitly wrapped converter has its own separately reviewed immutable wrapper and route bindings; changing a Registry record does not update those bindings. |
| Disable new strategy operations in a pool | New LP mint, increase and guarded swaps stop; typed collect/close remain available under custody, actual currency, runtime and real-key checks. Native V2 paths do not query WETH policy. Ordinary Vault exit validation ignores the source operations flag but still requires a valid oracle and acceptable spot deviation. Separately reviewed paused parking has raw-token authorization instead of a source USD read. |
| Move LP to another supported local pool | Governed `ZZZMigration.moveFunds` closes and redeploys the whole bucket through the Vault; `movePool` is an alias. Both pools must have identical actual ordered currencies and the destination must be admitted and enabled. Actual destination LP, unchanged shares and one fixed-price aggregate loss floor (3% default; governance maximum 10%) are required; gas separate. Another native ETH/ZZZ fee tier is supported. ETH and WETH are distinct; atomic conversion between those pools is not implemented and fails the pair guard. Use separately approved external custody/manual conversion and funded completion, or implement a reviewed boundary before sealing. Contribution pool/routes require deliberate cutover. |
| Convert principal into another local pair | The former pair executor is removed. Use separately approved external custody, perform the issuer exchange/conversion outside the source contracts and fund actual local destination LP through `completeLocal`. Normal mode retains the absolute floor recorded at approval (97% by default); raw mode uses its explicit destination minima. This is not an atomic arbitrary-pair `moveFunds` operation. |
| Park a paused shared LP during a source-price outage | Sealed, paused `ZZZMigration.park` requires the exact governance-approved LP/share/deposit/location/epoch/nonce snapshot, ordered currencies, reviewed close-only raw minima and a current deadline. It collects venue fees separately, closes the LP and keeps all principal attributed inside Vault. Old idle, donations and compound reserves cannot satisfy the close minimums. USD/sequencer reads and creator-inbox synchronization are omitted; actual core/token/runtime and venue bindings remain mandatory. Native V2 does not call WETH or its policy. |
| Resume parked principal | After unpause, governed `resume` requires valid valuation, an enabled destination with the same actual ordered currencies, actual LP and normal swap/idle/captured aggregate guards. Parking is not a bypass of destination validation. |
| Exit to external custody | Approve an exact request, pause globally and call `exit`. Normal mode consolidates attributed principal into configured ZZZ with stricter swap minima and the absolute approval floor (97% by default). Explicit `rawExit` sends both actual assets without swap/USD reads or a3% guarantee. Never downgrade normal failure automatically. Native V2 sends ETH/ZZZ without WETH, while venue/token/runtime failures can still block it. |
| Complete or recover external custody | `completeLocal` requires real approved destination assets and actual LP, preserving original normal/raw limits and shares. A sent local holding plan may bind one reserved destination through `bindLocalDestination`. `recover` requires all actual sent assets/quantities back into parked custody. Both require exact declared native `msg.value`, or zero ETH for an ERC20-only return; old prefunds are not funding. No timeout or accounting-only completion exists. |
| Use external custody for a future chain | The recipient receives on the source chain and may bridge externally. Remote confirmation/return requires a pinned reviewed finality/channel-closure verifier; no multisig-only or timeout override. No real verifier/provider/remote NAV or reward ledger is supplied. The old bridge path is removed. Canonical NFT/ledger relocation remains separate unfinished work. |
| Change keepers, guardians or strategy settings | Existing governed configuration and zero-delay controller; guardian pause is not asset-withdrawal or upgrade authority. |
| Change the Vault, reward ledgers or mint/trait rules after sealing | No generic implementation replacement exists. A new code version needs an explicit reviewed migration design; these configuration controls do not make arbitrary code changes safe or possible. |

## Configuration requirements not yet implemented

The user requires routine operating settings to stay configurable after seal.
The [bounded operating controls](POST_SEAL_POLICY.md) now implement future VRF
gas/confirmation tuning and a buyback operating ceiling beneath the immutable
hard maximum. Provider/lane/subscription/payment policy stays fixed; pending
draws and source economic rights are untouched. Entry and LP/royalty converters
now support explicit typed v3/v4 conversion; actual markets and services still require qualification. Preserve
earned rights, backing and execution floors; no reroll, arbitrary executor or sweep.

The ZZZ LP-reward conversion cap defaults to 1%, gas separate, and governance may set it up to 10%. The selected pool's
observed approximately 1.101% fee requires a cheaper independently qualified
conversion route. Unsupported conversion leaves source entitlements backed.

The [native V2 candidate](NATIVE_ETH_ARCHITECTURE.md) now implements actual ETH
funding, indexed fees, reserves, raw exit/return and canonical backing/abort.
Raw native exit avoids WETH but still needs usable venue/token/runtime bindings.
Atomic ETH/WETH conversion and V1 schema import are rejected pending explicit
reviewed boundaries. Real native markets/services, frontend profile, final
inventory and independent audit remain open before sealing.

## Permanent reservations and historical boundaries

`reservePool` and funded buckets share four permanent historical bucket slots.
Aliases/returns reuse a bucket; departure, cancellation or timeout cannot free or
reassign its reservation. Unfunded reservations have no shares or TVL. Verify
capacity and existing aliases first; governance can exhaust capacity. Local
reservation is not authenticated remote admission.

The former typed pair executor and v3 bridge/transport paths are removed.
[Pair-composition evidence](../reports/pair-composition/VERIFICATION.md) and
[architecture evidence](../reports/architecture-evolution/VERIFICATION.md) retain
their original source scope, not current bridge execution claims.

Whole-collection [canonical handoff](CANONICAL_HANDOFF.md) remains separate:
actual same-chain ownership, shares and both backed ledgers move to one reviewed
successor with atomic retirement/activation and funded abort. Outstanding
principal or royalty custody blocks capture. Pending mint draws must finish;
they do not block ordinary LP moves. Post-halt recovery remains deferred.

Royalty-currency custody uses its separate paused full-balance exit and exact raw
return. Original liabilities and quarantine persist; exited-currency claims and
valuation are unavailable, not zero. Restoration is not new income. Principal
exit never sweeps royalties, rewards, reserves, donations or mint payments.

A real-funds rehearsal uses a separate clearly named deployment and fresh final
collection. No public history/NFT/reward reset exists. Follow the
[rehearsal policy](POST_SEAL_POLICY.md#testing-with-real-funds-on-robinhood).

## Edge cases that remain release considerations

- **External custody failure:** a stopped chain, frozen asset, failed venue or
  unavailable bridge may prevent recovery. A hostile wrapper also affects an
  explicitly wrapped operation, but does not gate native V2 custody paths. No
  contract can guarantee movement through every failed external system.
- **Oracle outage:** ordinary upkeep and active-LP migration retain valuation
  checks. Governed token/sequencer feed replacement remains available. The
  [paused custody-parking path](CUSTODY_PARKING.md) now permits an exact,
  governance-approved close into Vault-held currencies without source USD or sequencer
  reads. Governance must review raw per-asset close minimums and a fresh custody
  snapshot; this cannot bypass a failed venue, frozen token or changed core/runtime
  binding. Native V2 parking does not use a wrapper. Resume requires recovered valuation. Recovery and local completion require actual funding and preserve the approved
  normal/raw limits; remote delivery additionally requires finality verification.
- **External custody:** sent plans cannot be erased or completed by timeout.
  Do not substitute unbacked tokens or forgive outstanding liabilities. Real
  finality verifiers and remote ledgers remain unsupplied release work.
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
