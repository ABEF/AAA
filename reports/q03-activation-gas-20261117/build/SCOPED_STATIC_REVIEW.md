# Proposed allocation library: focused source review

This is a fresh manual review of the proposed allocator and its actual consumers,
supported by the new differential experiment and closed compiler comparison. No
old Slither finding set or unchanged test suite is rerun or counted as new. This
is not independent audit approval or complete formal verification.

The proposed UTF8/LF source hash is
`22f42cbfd5220aa2605c048ea8809ad96c18c2f896e258293e9116af22f37b02`.
At compilation it is an explicit override; the other99 input sources exactly
match their raw filesystem bytes. Filesystem adoption and full-flow evidence are
separate later requirements.

| Area | Checked conclusion and boundary |
| --- | --- |
| Monetary arithmetic | Actual `Book.outstanding += amount`, `delta*count` and payout subtraction remain checked. Only coefficient/carry and bounded index arithmetic wraps. Solidity's checked and unchecked scopes are explicit; amount bounds do not inherit an unchecked caller context. [Solidity0.8.26 arithmetic](https://docs.soliditylang.org/en/v0.8.26/control-structures.html#checked-or-unchecked-arithmetic). |
| Complement arithmetic | For A=qW+r, credit(q+1) to the eligible prefix then remove one from the complementary W−r interval. That is exactly the original cyclic integer allocation, not fractional accrual. q+1 is evaluated only when W≥2. The temporary full-prefix aggregate may exceed UINTMAX; the actual economic amount never bypasses its checked bound. |
| Exact ticket ownership | Modulo path sums must equal nonnegative integer entitlements bounded by the checked aggregate. The aggregate alone does not establish correct ownership: correctness also depends on the private range/path invariant, checked against a fixed old positive engine and independent per-ticket arithmetic. |
| Payout path | Sibling propagation and path sums wrap consistently; the final `outstanding -= amount` remains checked. Removing a duplicate explicit comparison does not permit an excessive payout. A corrupted/impossible state can now produce Solidity's arithmetic panic rather than the prototype's custom error. No external writer can directly set lazy tags. |
| Bounds and termination | Existing interval guards remain. `cursor>=weight` rejects weight0 for every unsigned cursor, so removing the separate zero predicate preserves that rejection. Validated ticket/cursor arithmetic is bounded by3000; the4096-leaf tree traversal has bounded depth. No new external call or callback is introduced. |
| Clear and reuse | Final leaf deletion is unconditional; an already-zero warmed slot can cost100extra gas. Actual units and other tickets' rights stay unchanged. Partial claims, zero-entitlement paths, UINTMAX drainage/recredit and expanding eligible prefixes have finite new differential coverage. |
| Storage | All48 host ABIs match. Semantic layout comparison, ignoring AST type IDs, finds exactly one change: private Royalty `allocationBooks` values append `Book.outstanding` at slot1; the `pending` mapping stays at slot0. Other60 production source files and all39 dependencies are byte-exact. Layout changes need explicit compatibility review even when no public tuple changes. [Solidity storage layout](https://docs.soliditylang.org/en/v0.8.26/internals/layout_in_storage.html). |
| Canonical boundary | Royalty canonical rows flatten exact per-NFT units into accrued rights; they do not copy raw book tags. A fresh import therefore starts empty books/zero totals, keeping imported accrued backing separate. Historical nonempty raw books must never be reinterpreted as the new representation. Actual mixed-unit/canonical integration remains necessary. |
| Access and economic controls | Royalty host source is unchanged: NFT-only activation/admission, opening cutoff, isolated optional sync allowance, old-cohort recovery, current-owner claims, canonical/economic and reentrancy guards remain. Exact-LP's separate allocator is untouched. The all-fault16×1M gas exposure is not solved or disguised. |
| Size and embedded code | All48 normal runtime/initcode gates pass with the original constructor argument minima and unchanged compiler settings. Actual compiled royalty creation bytes produce legal two-part data carriers. These checks retain the [EIP170](https://eips.ethereum.org/EIPS/eip-170) and [EIP3860](https://eips.ethereum.org/EIPS/eip-3860) limits; dynamic constructor strings still need exact release-input qualification. |

The complete module build uses pinned native solc0.8.26, Cancun, viaIR, optimizer
runs1 and Yul optimization disabled. It does not raise a size gate, gas default,
financial cap, currency capacity or optional-sync budget. Observed temporary
Foundry file permissions for another rehearsal do not enter this standard-JSON
compiler input; their actual before/after hashes remain recorded rather than
being described as an unchanged base configuration.

Remaining obligations include actual whole-flow nearly1000-NFT cost with required
headroom, first-opening and unit2/3→unit1 behavior in the host, source/canonical
handoff, source-bound payload4 consumers, claims workload impact and independent
release review. The31-byte royalty runtime margin is tight; passing size checks
does not establish general future extensibility or production readiness.
