# Fee-breakdown backend verification

## Final source scope

Initial main `30eb4df`; five backend modules change, with three new regression
modules and one affected deterministic summary fixture. Production Solidity,
compiler/dependency/build settings and public wallet signing are unchanged.
No EVM, fork, static analyzer, browser or operating suite is repeated for these
Python-only changes. Earlier 399-finding static review and normal 37-object
gates remain reusable only after exact production/dependency bindings match.

## Reproductions and focused fixes

- [Profile evidence](PROFILE.md): seven original real-Projection methods expose
  accepted missing ETH and inactive positive balances; same fixture passes after
  correction. One later historical-profile method passes. Eight distinct new
  methods; unavailable currencies stay null and activated parked/outbound claims
  remain available when the view works.
- [Wallet summary evidence](OPERATIONS.md): initial malformed LP cases and later
  native ABI/inactive state contradictions are preserved. Final scoped run covers
  11 new plus 12 existing summary methods. Its shared fixture and finite-call
  bound are updated for the one additional weight read, not relaxed.
- [History evidence](HISTORY.md): exact raw SQLite/API gross100→200 and dust100→119
  counterexamples, omitted fee events and wrong actual version reproduce before
  the fixes. Final test module has 12 distinct methods, including independent LP/
  rarity weights, top-up, native carried dust, legacy behavior, multiple receipt
  pairs/interleaved royalties and current canonical epoch import/reset. Earlier
  semantic/dust/canonical reruns overlap; they are not additional final coverage.

## One final affected regression sweep

[Result](affected-suite.json), [log](affected-suite.log) and
[runner](run-affected-suite.py) record **167 / 167 distinct methods passing**:

- 31 new methods and 136 affected existing methods, 22 actual defined classes
  across the 10 selected modules;
- zero failures, errors, skips, expected failures or unexpected successes;
- 29.563s elapsed, with all 54 implementation/fixture/runner inputs hash-bound
  and unchanged before/after;
- imported TestCase classes and duplicate IDs excluded; unrelated dirty history
  test methods are not selected. Its imported HistoryRPC helper is unchanged
  from committed HEAD; the original file's two unrelated added tests are preserved;
- actual Projection/ABI parsing, disposable SQLite, synthetic RPC and ephemeral
  loopback HTTP fixtures; no actual public/provider RPC, signing, existing state
  or operating-service mutation.

This is an affected backend regression, not the entire repository's Python
suite, a fresh full release regression, actual provider qualification or an
independent audit. Earlier focused counts are subsets/previous source scopes
and must not be added to 167. No failed assertion is silently waived.

## Financial assertions

NFT net income is exactly individual LP + equal collective LP + eligible
rarity-weighted royalties. The fixed current fee grammar matches the actual
funded credit and carried dust before accepting gross/reserve totals. The
1:3:2 LP / 3:1:2 royalty example asserts 400/360/380 from 1,200 total inflow,
with 60 separately reserved; later top-up preserves past earnings and royalty
weights. Gross receipts and reservations are not additional NFT income.

Current claimable, original-currency earned history and lifetime actual payouts
remain distinct. Existing cases protect current-price valuation, missing prices,
fractions/dust, transfers, claims/conversion denomination changes, late royalty
eligibility and same-chain lineage. Optional outages remain unavailable; malformed
core values, impossible inactive entitlement and missing current ETH inventory
reject rather than fabricate or partially sum a complete amount.

No financial economic rule is changed by stronger reader validation. Source
funding, correct on-chain implementation and authentic complete indexed history
remain explicit trust and release requirements.

## Final non-test checks

Final manifests verify the actual five backend hashes, new/shared test hashes,
44 unchanged production sources, 31 normal dependency sources and four build
inputs. Callable-reference freshness, sole Todo generation, current unchanged
static-review coverage and local Markdown targets are checked; source consistency
is output only to this campaign. Original 14 dirty-file suffixes stay byte-identical.
These checks are bookkeeping, not extra financial execution tests.

Documentation/operator/Todo/features/roadmap/release/context updates explain the
new reads, fail-closed behavior and no automatic replay repair. Publication and
its receipt are separate from any deployment. Production remains NOT APPROVED.
