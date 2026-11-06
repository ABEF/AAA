# Verification scope and retained evidence

6 November 2026; starting main11e0157. [Findings](REVIEW.md).
Production NOT APPROVED. No operating environment was changed.

## New actual local-v4 evidence

[Accounting record](accounting/FINAL_TEST_REVIEW.json): **3distinct new methods**
pass across recorded stages: two actual-core methods and one real-ledger method
with isolated share custody. Initial selection ran3:2passed; the third failed
because the independent expected model combined two receipts across a real dust
flush. The corrected model processes each receipt/barrier separately. A later
anchored name matched0tests; that attempt is retained as empty, not a success.
The corrected exact1-method selection then passed. The prior two unchanged
successes were not rerun or counted twice. Their
[transitive reuse proof](accounting/INITIAL_SUCCESS_REUSE_PROOF.json) binds exact
initial/final source snapshots, unchanged helpers/setup/scaffold and189other
compiler dependencies; the added helper is used only by the corrected method.

New cases cover actual main/residual fee-growth collection,64fragmented versus
one final harvest, final finite Rewards/FeeController rounding, second-leg
failure rolling back the first, funded incumbent/entrant separation through
activation and growth, separate20unit/flush arithmetic, reserve separation,
unchanged residual and current-owner transfer/claim/no-repeat.

The new fixture uses real installed core/periphery with mock Access/admission,
token/VRF/Permit2 and explicitly correlated test feeds. Donations create actual
core fee growth, not organic market activity.190source ABI/type closure passes
at its recorded initial stage. Selected test envelopes/cache are isolated; their
larger test-contract allowances are not production size or target gas approval.
All preexisting test files and production Solidity bytes are preserved.

## Keeper implementation evidence

[Services record](services/SERVICES_EVIDENCE.json): **73unique focused methods**
pass on the final diagnostic source,16new and57affected existing.0failures,
errors or skips. New timing and restored-wrong-bucket regressions also fail
against exact baseline monitor bytes in an isolated process, proving sensitivity.

Coverage includes hourly/override/historical defaults; successful slow reads;
failed fresh head; no extra skipped-job head; exact current4/5/6 key/call/event
proof;0/0and positive receipts; malformed/foreign/duplicate inclusion; reverts,
pending/hashless work, canonical change, failed atomic save, restart/idempotence
and paid fee/nonce recovery. The added sanitized warning is asserted once for
the inconsistent saved-bucket case.

An earlier new-only run had intended invalid block/transaction hashes equal to
the fixture's valid hash; those negative fixtures were corrected and retained.
Earlier73-source and final-diagnostic73sets overlap completely and are not added.
Mocks and temporary journals do not qualify a Linux service, real provider,
funding, target latency or uninterrupted operation.

## Exact-unit design verification, NOT production implementation

[Design record](design/DESIGN_EVIDENCE.json): **20isolated model methods** pass.
The lazy weighted tree is compared with an eager cumulative-left oracle under
the SAME declared hierarchical rounding policy. Cases cover1000ordinals,
finite1unit/101shares, both80/10components/assets, shares/activation, sibling
protection, transfers, claim order/batching, overflow and empty cohorts.

An independent review found that the eager oracle wrongly reset its stream on
an unchanged weight. The pre-correction counterexample is retained; final20adds
the no-op regression and corrects the oracle. Earlier19is not final20and counts
are not summed. The initial overflow-negative vector also did not exceed uintmax;
its inadequate assertion is retained and corrected, not hidden as a model pass.

Hierarchy and flat proportional rounding are demonstrably different: weights
2/1/2with3units yield0/1/2under this tree versus1/0/2under flat cumulative floors.
This is disclosed design policy, not a proof of optimal fairness. The model does
not implement Vault hooks, actual Solidity/gas, LP conversion/canonical formats,
all dust barriers, frontend/API or an upgrade to current deployed rights.

## Source gates, documents and preservation

Production Solidity/dependency/build pins are checked against the accepted
moving-market normal84-source closure.44normal compiler objects plus2actual
carrier gates and497strict static records remain their EXACT prior evidence;
no unchanged normal compiler, Slither or full contract suite is rerun or labelled
new analysis here. Current function/operator reference and generated Todo checks
remain required. [Local checks](local-checks.json) and [preservation](preservation.json)
record actual outcomes, source hashes and explicit exclusions.

The new test/prototype, keeper fixes and current documentation are distinct.
Original report bytes, four unrelated dirty tracked files, other drafts and
website state are preserved. Pending nonces/receipts/spend, existing Anvil holdings,
dist overlays, signer/public-null deployment and paused heartbeat are untouched.
No public CI, actual token/feed/route/burn/marketplace, operating gas/restore or
independent approval follows from this scoped evidence.
