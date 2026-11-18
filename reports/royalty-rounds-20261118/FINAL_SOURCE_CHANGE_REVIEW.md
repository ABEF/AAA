# Final source and accounting review

The C08 final actual build is `build/final`, separate from the earlier phase1
`build/current` and C07 `build/c07`. It compiles the exact100 current raw sources under the unchanged
normal compiler/settings, passes48 runtime/initcode gates and the strict compiler
artifact importer, and binds the same four build-input files. Phase1 sizes,
layouts, sources and results remain historical evidence.

## Rights and private layout

Round allocation keeps the earlier verified whole-unit equations, cohort-birth
snapshots, homogeneous rarity phases, imported accrued separation and checked
currency liabilities. Canonical records stay flattened with identical wire rows;
settlement4/recovery2/allocation2 remain. LP allocations,80/10/5/5, rarity weights,
ownership, claim destinations and operating authority do not change.

The duplicate `accounted` cache is replaced by the checked identity
`liabilities + orphaned + openingPool`. Every accounting path retains those exact
categories and backing checks. Private slot24 is removed; all later Royalty
fields shift exactly one slot, as verified in
[the compiler-derived baseline/phase1/final comparison](FINAL_STORAGE_COMPATIBILITY.json).
This is a fresh Factory5 representation, not a hot upgrade, raw-tree import or
permission to reinterpret an older live deployment's storage.

C08 corrects an additional derived-accounted boundary: an unused target may
already contain a publicly synchronized pre-sale opening balance. Import classifies
the target's entire actual prefund as orphaned once, clears its old opening pool,
and constructs orphaned as `(sourceAccounted + actualPrefund) - sourceLiability`.
The existing checked source identity and total-prefund overflow bound remain;
no external call intervenes. Imported source earnings remain liabilities, and
`initialAllocated` remains true. This replaces a tautological derived equality,
not the financial total-overflow guard. A cached pending-view prior removes only
an adjacent duplicate read while retaining its explicit underbacking check.

`_syncBalance` has mutually exclusive pre-opening, initial-opening and positive
ordinary-receipt branches, followed by one common enrollment tail. Their credits,
events and event order are unchanged, including the zero-receipt path. A cached
prior accounted value retains the explicit underbacking check and checked delta.
`_allocationUnit` reads the three immutable first-rarity ordinals once. Its active
bits are exactly `first != 0 && first <= count`; common presence or Rare+Legendary
gives1, Rare-only2, Legendary-only3, and none0. This is the same eight-case rule.

## Optional read funding

Activation captures the governed complete-sync and balance-read maxima once.
Only the authenticated self-call carries a packed cap/full-frame witness. A full
frame retains the original1M maximum and120k caller-funding witness. A partial
frame must independently reserve the read cap plus the same120k before STATICCALL,
so caller clipping cannot manufacture a gas-sensitive balance result. The fixed
32-byte copy still accepts ABI-compatible padded output and rejects short reads.

Only that fixed child converts a fully funded unavailable/underbacked read into
the dedicated4-byte `ActivationReadUnavailable` signal. Token revert bytes are
never bubbled. Outer classification requires exact selector and length. Other
partial-frame failure reverts the whole activation; fully funded complete-frame
failure retains old deferral. Successful accounting actually completes before
new enrollment. Known outages preserve the old eligible cohort and its receipts.

The public economic ABI/events are unchanged. The self-only helper gains its
explicit `uint256 readLimits` input and dedicated error; Assets adds read-only
`validateInput(address)`. Entry/Assets retain all admission, price/minimum and
funding rights; Manager/Pricing reuse only proofs separated by STATIC/local work,
as detailed in PLACEMENT_PROOF_REUSE_REVIEW.md and entry/REVIEW.md.

Final headroom is Royalty4 runtime bytes, Oracle3, Vault32 and Manager117; Access
creation plus96 constructor bytes leaves562 initcode bytes. Tight margins remain
a material maintenance constraint. Component/placement passes do not establish
launch-scale gas, real market/provider/fees or independent release approval.
