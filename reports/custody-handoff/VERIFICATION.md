# Governed custody handoff: verification record

Development candidate, contracts undeployed, production **NOT APPROVED**.
Final scoped local checks are recorded below. Git publication is recorded
separately; passing local checks is not production release approval.

## Authorized scope

The user approved governed external custody for pool/token/chain migrations,
removal of old LP bridge/pair paths while retaining the whole-collection handoff,
normal all-ZZZ consolidation, an explicit no-swap emergency transfer when markets
cannot meet the loss budget, and inclusion of separate marketplace royalty
currencies. Governance explicitly trusts EOA/contract recipients after transfer.
Source contracts cannot force an external custodian to return funds.

## Implemented boundary

- One fixed Migration module governs exact per-bucket approval, all-ZZZ exit or
  separately approved raw exit, actually funded local LP completion and full raw
  recovery. Normal mode retains one original 97% fixed-price floor through exit
  and local redeployment. Raw mode uses explicit token minima and has no USD-loss
  guarantee. Holding without a selected destination pool is explicit and remains
  pending; a sent local holding plan may bind one admitted/reserved destination
  later without rewriting its original mode, departure or loss budget. There is
  no automatic downgrade, timeout refund, arbitrary call or sweep.
- NFT shares/ownership and historical LP/collective/royalty rights remain.
  Donations, another bucket and fee/royalty ledgers do not subsidize principal.
  Pending compound/buyback reserves are separate. The approved local destination
  must already be reserved for this same bucket before departure.
- Cross-chain delivery/return use separately domain-separated commitments and
  pinned finality/closure verifier code. No governance-only override. No real
  verifier/provider/remote revenue ledger/canonical chain relocation is supplied.
  A fixture verifier tests the interface/guards, not actual consensus security.
- Marketplace currency custody is separate: paused governance moves an exact
  full admitted balance, preserves all NFT liabilities/quarantine and makes that
  currency explicitly unavailable until fully funded raw restoration. Healthy
  currencies/LP claims and ownership transfers retain their own paths. Returning
  custody is not new income; deferred eligibility excludes newcomers from older
  receipts, including the native-currency custody case.
- Governance can review/configure future ZZZ and separately update the buyback
  target. Existing strict acquired-balance and actual burn checks remain.
- Old v3 bridge/router/receiver/registry and pair-executor implementations are
  removed. Their source/tests are historical text in `reports/history/retired-v3-*`;
  they are not passing current cases. Retired receiver/bridge module IDs cannot
  be bound in the new controller. Legacy Vault import selectors fail closed.
  Same-chain whole-collection handoff is retained with 16 required module bindings.

## Checks and diagnostics

Focused custody/parking run: **37 cases passed**, including 1,000 fuzz samples
of exit loss, full/partial funding, no automatic raw fallback, stale prices,
original NFT shares, late creator fees, proof/closure guards and royalty custody.

Retained same-chain whole-collection run: **34 cases passed**, including the full
1,000-NFT inventory, multiple assets/buckets, ownership and both ledgers, partial
funding, abort, replay, native rewards and onward same-chain replacement. This
has its own exact source scope; subsequent custody-only/event refinements do not
turn it into a fresh full final-source regression.

Python release-gate checks: **150 passed** (147 existing inventory checks and
three new explicit-block checks). The new candidate template is intentionally
**blocked** until a separately reviewed release inventory supports this layout.
This does not qualify any real deployment or replace live observations.

Final affected source: **64 cases passed, zero failed/skipped** in four suites
(24 custody handoff, 9 royalty custody, 11 parking, 20 access-control). The two
fuzz cases each used 1,000 runs. Exact source hashes and raw output are in
[runs/test-current-fixed.json](runs/test-current-fixed.json) and its log. This
covers the final read-only helper extraction and delayed local destination binding.

Earlier broader run: **183 passes** in 15 suites, including shared accounting,
maintenance budgets and external-funding invariants. Its own source scope is in
[runs/test-final.json](runs/test-final.json); it predates the last helper/binding
refinement and is not a fresh full final-source regression. The 34-case retained
canonical run also keeps its earlier source binding. Counts are not added together
as unique coverage or represented as a full new regression.

**33 compiled source-object runtime/initcode gates pass**, using unchanged
0.8.26/Cancun/via-IR optimizer settings and normal EIP-170/EIP-3860 limits. Migration
runtime is **23,754 bytes**, with **822 bytes margin**; initcode is 33,252 bytes.
See [object gates](size-gates.json) and [build command/source binding](runs/build-core.json).
Objects exclude constructor argument bytes/live immutable deployment hashes.
The changed local-only deployment scaffold also compiles successfully; it was
not executed or broadcast. [Compile receipt](runs/scaffold-build.json).
The immutable view-only validator checks admission; it has no asset execution.
Its mirrored Request ABI matches the parent's exact field order.

The three new Python custody-inventory block cases pass again; the earlier 150-case
Python result includes those plus 147 legacy gate cases and retains that scope.
Source consistency reports 38 source files with no errors. Todo and scoped local
file links are checked independently. None of these grants release authorization.

Diagnostics retained: initial 182-case run had 180 passes/two stale expectations
(park before release; reject sub-$5 top-ups). The corrected 183-case run preserves
the production minimum. The first final 64-case run had one test-fixture error:
`expectRevert` intercepted an intermediate helper getter, not validation. Caching
the helper before the expectation corrected the fixture; production guards did
not change. Initial oversized builds and the final size refactor are explicit.
Sandboxed Forge could not access its normal Windows signature cache; the offline
build completed with reviewed tool-cache access. An obsolete compilation was
cancelled earlier and is not a passing check. Existing compiler/lint warnings are
not presented as a clean independent static-analysis review.

## Operational and publication boundary

No public deployment/transaction, no wallet key use, no local Anvil/NFT/LP/balance/
journal reset, no website build/deployment and no paused-monitor change. Tests
run in Forge's isolated VM with explicit fake venues, feeds/tokens and VRF.
Existing 8902 state and its temporary dist repair overlay remain untouched.
The shared website signer stays Anvil-only and public DEPLOYMENT stays null.

The source's future remote verifier/bridge/ledger, unsupported native/hooked
destinations, real exit depth/routes/feeds, host/keeper/API pending-custody status,
gas/operating rehearsals, governance custody disclosures, new release inventory
and independent audit/remediation remain open. Full royalties converted/remapped
onto a remote ledger is not implemented by temporary raw custody.

Internal review: [boundaries and remaining risks](REVIEW.md).

Procedure: [operator runbook](../../docs/GOVERNED_CUSTODY_HANDOFF.md).
Status: [sole Todo](../../TODO.md#task-custody-composition).

Publication: [main-branch receipt and unchanged deployment boundary](PUBLICATION.md).
