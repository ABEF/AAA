# Keeper coordination and truthful operation diagnostics

Reviewed 2026-10-29 against main `981207e`. This implements the user's selected
service policy and requested harvest/report improvements. It preserves the
operating model: entrant-only contributions, incumbent checkpoints, marginal LP
and net-NAV share issuance; separate harvest, conversion, compound, buyback and
claims; whole-LP replacement versus same-range reinvestment; independent reward,
parking, terminal-return and canonical permissions/accounting.

**Source only; production NOT APPROVED.** No Solidity, installed service, site,
Anvil, signing policy, key, transaction journal or public transaction changed.

## Delivered changes

| Area | Behavior and boundary |
| --- | --- |
| Compound scheduling | Fresh accounting4/policy2 waits while the actual LP is outside its physical ticks or an operator width change is pending, including before the hard rebalance interval. Authenticate LP identity/custody, exact slot0/ticks, modules and width at a canonical hash; recheck before a new intent. Missing reader bindings are unavailable, including explicit older LP0 worker configurations, rather than a guessed in-range fallback. |
| Existing contract guards | Budget readiness, separate compound interval, raw rebalance priority, approved routes/prices, exact balances and all financial caps remain. A Python policy is bypassable by another authorized key; it does not create an inclusion-time on-chain in-range guarantee. |
| Confirmation coordination | A live worker's proved inside/opposite-side observation cannot preserve a known nonempty ordinary outside window. Same-hash helper evidence feeds existing durable reset/ack scheduling; foreign nonempty evidence after a clear is forced once. Empty/manual/cleared evidence must not cause repeated paid resets. Pure physical readers and the diagnostic command never mutate this state. Missing configuration is separate from an interrupted raw physical read. No new timer or namespace. |
| Harvest coalescing | Canonical own successful compound/rebalance receipts with exact matching Vault FeesCollected proof update the existing per-bucket harvest clock inside the paid nonce/spend save. Zero fees and multiple legitimate events are supported. Missing optional proof preserves paid recovery and leaves the clock unchanged. No adoption from submission, NAV or unjournaled activity. |
| Read-only report | One to four explicit bucket IDs; rebalance, compound and harvest only. Separate not-needed/timing/known-blocked/unavailable/unconfigured states. Fixed typed optional simulations, estimated gas caps and native gas funding. Actual financial policies are observed; unmeasured USD/swap margins stay unavailable. No arbitrary calls, signer, nonce recovery, journal creation or scheduler mutation. |
| Actual-ABI preflight repair | The prior observer called a nonexistent public getter for Vault's private registeredBucket mapping, hidden by its synthetic fixture. Registration now derives from this run's complete pinned-hash bucketAt inventory. Missing/stale/incomplete evidence cannot become false/unreserved. No new Solidity getter or ABI change. |

The report distinguishes permissionless contract fee collection from the worker's
own keeper authorization requirement; preparation stops compound/rebalance but
does not incorrectly disable otherwise valid harvest. LP custody checks for
harvest do not depend on slot0/oracle/width observations. Detectable same-hash
position contradictions invalidate the report rather than mix financial/timing
bases. Hex-data spelling is normalized without weakening ABI bounds.

`ok:true`/exit zero means a report was produced. `observed_eligible` covers only
evaluated prerequisites; `simulated` additionally covers a discarded call and
estimated caps/funding. Neither means ready to sign, included, actual paid cost
or production approval. A generic provider revert remains unclassified. Jitter
and future inclusion are not invented from a timing lower bound.

## Idle and financial vocabulary

Idle is attributed ETH/ZZZ outside the physical LP, not an operator surplus or
claimable fees. Released compound joins incumbent idle; entrants deploy only
their own budget. The separate 5% whole-bucket ceiling can therefore block entry
even if an entrant passes its marginal LP floor. Waiting outside can extend that
tradeoff; it does not authorize an automatic emergency, sweep or wider cap.

The swap-output floor applies to tokens actually sold; the pre-add-LP buffer
floor applies to retained ETH+ZZZ; the contribution floor applies to actual new
LP (default $98 per $100); the maintenance floor applies to starting principal
plus released compound (default 3%). Conditional numerical overlap does not
prove one redundant under rounding, price timing or retained emergency checks.
No floor was removed. See the [operator guide](../../docs/KEEPER_COORDINATION.md).

## Review and retained counterexamples

Independent review corrected the prototype physical-owner assumption (LP is
owned by Vault, not Manager), optional-header spelling/late freshness, mixed ABI
case, harvest custody independence and mixed-snapshot reporting. The old private
getter mistake is acknowledged explicitly: historical mock success was not live
observer feasibility. [Repair](RESERVATION_REPAIR.md) and [ABI membership](abi-signatures.json)
bind the corrected calls to actual source-bound compiler interfaces.

Intermediate campaign/test-fixture errors remain in the external evidence
directory. The first combined campaign had actual report-test drift plus a
runner-inventory flaw that mistook lazy imports for changed files; it was not a
passing final campaign. The runner now captures the whole Python source pool
before bodies execute and still rejects actual byte drift. Overlapping probes
are never added to coverage.

## Operating and release limits

Install matching worker/checker source through a separately authorized controlled
rollout, retaining original pending/spend/nonce evidence. The new helper is in
local source fingerprints; these are not runtime attestation. No process or site
was restarted. Extra pinned reads and serial nonce/reset/harvest timing need real
RPC/host/gas qualification. The report's work budget is cooperative, not an
absolute DNS/socket watchdog.

Remaining adapters, actual feeds/routes/VRF/authorities/OpenSea, current website
and service acceptance, economics/ordering/target gas and independent audit stay
in the [sole Todo](../../TODO.md). [Verification](VERIFICATION.md) distinguishes
fresh execution from exact unchanged Solidity/build reuse.
