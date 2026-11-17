# Reservation identity admission — focused source and behavior review

The operator explicitly approved restricting **new** pool reservations to the contract-calculated custody identity, while retaining aliases to registered buckets. This closes a confirmed setup trap: an arbitrary nonzero identifier could permanently consume one of four historical slots and prevent initial activation. No live instance is changed and no existing reservation is rewritten or released.

## Final implementation

`MigrationBudget.validateReservation` retains Vault-only authorization, nonzero inputs, admitted-pool lookup and existing mapping checks in their original order. Existing wrong reassignment still fails with `InvalidState`; the same mapping stays idempotent. For a previously unbound pool, it reads the fixed bound `Migration.validation()` child and requires `CustodyValidation.validReservationIdentity(pool,bucket)`.

That **public read-only identity predicate** accepts the authoritative `VaultCanonical.bucketIdentity(pool)` (preserved origin chain/Vault), or a bucket actually enumerated by the Vault's registered list. The list is explicitly bounded at four. Everything else fails before `_registerBucket` or `registerAlias`. A true identity result alone does not authorize a write or admit an unknown pool; Budget retains those outer checks. No custody address, new deployed helper, storage field, split, timing, bypass or principal/reward right changes.

Empty registered buckets remain valid alias targets under the approved rule. Such an alias does not turn a different pool into a new initial activation domain; actual pool movement still needs an existing eligible position. Canonical import continues through its authenticated writer and preserves imported aliases. No new guard is inserted into historical import records.

## Size constraints shaped the placement

The first direct Budget implementation exceeded the normal runtime limit by 103 bytes. A two-object probe moved the predicate to VaultCanonical: Budget fit, but VaultCanonical exceeded the limit by 79 bytes. Both rejected stages are retained; no size gate/compiler setting was weakened.

The final predicate lives in the existing fixed `CustodyValidation` child, which has room and already owns operational custody checks. A normal-settings three-object size probe reports Budget **24,507/24,576**, CustodyValidation **18,868/24,576**, and Migration creation **44,334 + 32 arguments /49,152**. These probes are not the full normal 48 gates; the root full build/analysis remains separate. VaultCanonical is restored byte-for-byte.

## Test and fixture work

- Two new actual local v4 methods cover typo rejection with zero capacity/alias effect followed by canonical activation, and registered alias reservation followed by actual native pool move/return. They preserve share identities, funded claims, Vault LP ownership and protocol reserves.
- Two new focused methods verify authoritative imported origin (real companion, explicit mock phase/authority seam), existing-map behavior even with a failed identity reader, and unauthorized reservation/Budget calls.
- Ten affected capacity methods now reserve actual companion-derived identities instead of retired synthetic foreign IDs. They cover all four slots, fifth rejection, first/last bucket aliases at capacity, no reassignment, inactive reservations, staleness and future activation.
- One obsolete pooled-security scenario and one full-capacity pool-switch scenario are adapted to the new admission rule.

The first provisional capacity run recorded eight passes/four activation failures. It was at the rejected oversized source and is not final evidence. Investigation found that the older shared fake venue lacked the current executionStrategy reader. The test-only adapter now preserves its declared synthetic geometry/price seam but delegates maintenance valuation/loss/idle/readiness to **actual production LP math**. All instantiated replacements are wired; the six current harness families using `Migration = this` expose the real fixed validation child. This is fixture maintenance, not unconditional success responses or relaxed production guards. Historical text fixtures remain historical.

Only the 16 new/affected methods are selected here. Actual v4 still uses controlled authority/admission/Permit2/VRF and price fixtures; deterministic capacity cases do not qualify live pools or production gas. Larger gas/fork suites are not rerun or relabelled. Exact results and source stages are recorded separately after verification.

## Selected results

**16 distinct methods have passing evidence: four new and twelve adapted.** New actual-v42, imported-origin/authority2, capacity10 and the two adapted pooled/switch cases are counted once. No full lifecycle/gas/fork/invariant suite is rerun by this reservation portion.

Eight reservation-only methods passed before the test adapter gained its required `fixedZZZ` read. The four failing activation cases then passed after that exact forward was added; the diagnostic trace identifies the missing selector at `Oracle.beginExecution`. The eight successful cases were not repeated. Their prior full test artifact was overwritten, so the prior helper is explicitly reconstructed from the one-line difference rather than falsely called retained original compiler evidence. Current4 activation + actual-v42 + pooled/switch2 have complete final compiler metadata/source proofs.

The raw staged results, both rejected size attempts and the failure trace are retained. [Fixture maintenance scope](RESERVATION_FIXTURE_SCOPE.json) distinguishes source-only updates from executed cases; historical cold-gas and fork evidence is not relabelled. [Verification](RESERVATION_VERIFICATION.json) records exact names and source stages.
