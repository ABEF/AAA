# Reservation observer ABI repair

The previous observer called `registeredBucket(uint256)`, but the production
Vault's mapping at `src/ZZZVault.sol:37` is private and has no ABI getter or
fallback. Its synthetic RPC fixture invented that selector. Actual observation
would therefore fail closed as unavailable; earlier mock success was not
evidence that this read could work against the source-matched Vault. This review
initially missed the ABI mismatch and corrects that assessment explicitly.

The repaired observer uses only real public getters. It retains a private,
per-run proof of successful complete `bucketAt` enumeration at the pinned hash.
It rejects zero/duplicate IDs, missing/failed enumeration, stale configured
observations, changed anchors, or a later count/max mismatch. `target_registered`
is explicitly **derived** membership in that authenticated complete inventory,
using `_registerBucket`'s atomic flag-and-push/no-removal source invariant. Missing
evidence never defaults to false. No Solidity getter or source change was added.

The new ABI regression uses the checked-in source-bound compiler ABI, verifies
every production/dependency source hash, rejects unsupported Vault selectors,
and verifies the healthy observation succeeds through that boundary. The ABI
export was independently compared with exact build-attempt-011 compiler output.
The unsupported-selector negative fails before repair (`0x745a059f`); two other
new methods reproduce stale/incomplete inventory failures. Positive controls
retain empty, canonical-slot/capacity, moved alias and imported lifecycle cases.

Verification scope:

- Three new regression methods fail before repair, for the intended ABI and
  inventory reasons. Subtest assertions are not additional methods.
- Twelve reservation methods pass after repair and again at final pins after
  the single separately authorized diagnostic-text correction. Count them once.
- Sixty-four other affected v4 inventory, physical-confirmation and final-depth
  methods pass before that diagnostic-only change. Their executed source pins
  remain in `final-affected.json`; they were not broadly rerun or relabelled as
  final-byte execution.
- `final-source-pins.json` lists all76distinct affected method IDs and the exact
  final four-file hashes. All78production/dependency texts and original compiler
  artifacts remain unchanged. No build, EVM execution, service, key or network
  transaction was used.

Original sources, commands, stdout/stderr and negative/final source hashes are
retained externally under keeper-coordination-20261029/financial/reservation-repair-001; selected receipts are copied here. Earlier published221-method evidence remains its own
historical source/mock scope and is not rewritten by this correction.
